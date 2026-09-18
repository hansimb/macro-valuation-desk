"""Bounded historical driver for the US country-index weekly flow.

The backfill owns date iteration only. Each complete Monday-Friday window is
delegated to the already validated Task 10 flow and receives a deterministic
run identity and checkpoint directory, making ``--resume`` safe and auditable.
"""
from __future__ import annotations

import argparse
from datetime import UTC, date, datetime, time, timedelta
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Callable, Sequence

from src.flows.us_country_index_flow import run_us_country_index_flow
from src.tasks.run_us_country_index_etl import DEFAULT_METHODOLOGY


class BackfillConfigurationError(ValueError):
    pass


FlowRunner = Callable[..., dict[str, object]]


RECEIPT_VERSION = 2


def _receipt_path(checkpoint_dir: Path, identity: dict[str, object]) -> Path:
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16]
    return checkpoint_dir / f"{identity['market']}-backfill-{identity['week']}-{digest}.receipt.json"


def _json_result(value: object) -> object:
    return json.loads(json.dumps(value, default=str))


def _complete_weeks(from_date: date, to_date: date) -> tuple[date, ...]:
    if from_date > to_date:
        raise BackfillConfigurationError("--from must be on or before --to")
    if from_date.weekday() != 0 or to_date.weekday() != 4:
        raise BackfillConfigurationError("backfill bounds must cover complete Monday-Friday weeks")
    if (to_date - from_date).days % 7 != 4:
        raise BackfillConfigurationError("backfill bounds must cover complete Monday-Friday weeks")
    return tuple(from_date + timedelta(days=offset) for offset in range(0, (to_date - from_date).days + 1, 7))


def _run_country_flow_week(**kwargs: object) -> dict[str, object]:
    week = kwargs["valuation_week"]
    checkpoint_dir = Path(kwargs["checkpoint_dir"])
    resume = bool(kwargs["resume"])
    run_id = f"{kwargs['market']}-backfill-{week.isoformat()}-{kwargs['methodology_version']}"
    if not resume and any(checkpoint_dir.glob(f"{run_id}.*.json")):
        raise BackfillConfigurationError(f"checkpoint exists for {week}; rerun with --resume")
    # Task 10 evaluates the previous complete week relative to its clock.
    clock_value = datetime.combine(week + timedelta(days=7), time(12), UTC)
    result = run_us_country_index_flow(
        market_id=kwargs["market"],
        methodology_version=kwargs["methodology_version"],
        environment=kwargs["environment"],
        run_id=run_id,
        checkpoint_dir=checkpoint_dir,
        clock=lambda: clock_value,
    )
    checkpoint = checkpoint_dir / f"{run_id}.validation.json"
    if result.get("status") == "success":
        envelope = json.loads(checkpoint.read_text(encoding="utf-8"))
        result["backfill_provenance"] = {
            "task_checkpoint": str(checkpoint.resolve()),
            "task_checkpoint_fingerprint": envelope["fingerprint"],
        }
    return result


def _source_provenance(runner: FlowRunner) -> str:
    explicit = getattr(runner, "receipt_source_provenance", None)
    if explicit:
        return str(explicit)
    factory = os.getenv("MVD_US_COUNTRY_INDEX_PROVIDER_FACTORY")
    return f"provider_factory:{factory or 'unconfigured'}"


def _receipt_identity(*, week: date, environment: str, development_prices: bool,
                      methodology_version: str, runner: FlowRunner) -> dict[str, object]:
    return {
        "market": "us",
        "week": week.isoformat(),
        "methodology_version": methodology_version,
        "environment": environment.lower(),
        "development_prices": development_prices,
        "source_provenance": _source_provenance(runner),
    }


def _load_receipt(path: Path, expected_identity: dict[str, object]) -> dict[str, object]:
    try:
        envelope = json.loads(path.read_text(encoding="utf-8"))
        if envelope.get("version") != RECEIPT_VERSION or envelope.get("identity") != expected_identity:
            raise ValueError("identity mismatch")
        result = envelope["result"]
        provenance = result["backfill_provenance"]
        checkpoint = Path(provenance["task_checkpoint"])
        task_envelope = json.loads(checkpoint.read_text(encoding="utf-8"))
        if task_envelope.get("fingerprint") != provenance["task_checkpoint_fingerprint"]:
            raise ValueError("Task 10 checkpoint fingerprint mismatch")
        if result.get("status") != "success":
            raise ValueError("receipt is not successful")
        return result
    except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError) as exc:
        raise BackfillConfigurationError(f"invalid backfill receipt {path.name}: {exc}") from exc


def _write_receipt(path: Path, identity: dict[str, object], result: dict[str, object]) -> None:
    provenance = result.get("backfill_provenance")
    if not isinstance(provenance, dict) or not provenance.get("task_checkpoint_fingerprint"):
        raise BackfillConfigurationError("successful backfill result is missing Task 10 checkpoint provenance")
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps({"version": RECEIPT_VERSION, "identity": identity, "result": result}, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    os.replace(temporary, path)


def run_backfill(
    from_date: date | None,
    to_date: date | None,
    *,
    market: str,
    resume: bool = False,
    development_prices: bool = False,
    environment: str = "development",
    methodology_version: str = DEFAULT_METHODOLOGY,
    checkpoint_dir: str | Path = ".mvd-checkpoints/backfill",
    flow_runner: FlowRunner | None = None,
) -> dict[str, object]:
    if from_date is None or to_date is None:
        raise BackfillConfigurationError("a bounded backfill requires both --from and --to")
    if market.lower() != "us":
        raise BackfillConfigurationError("this gate supports only --market us")
    if not methodology_version:
        raise BackfillConfigurationError("methodology_version is required")
    if environment.lower() == "production" and development_prices:
        raise BackfillConfigurationError("development prices cannot be used for production publication")

    weeks = _complete_weeks(from_date, to_date)
    runner = flow_runner or _run_country_flow_week
    target = Path(checkpoint_dir)
    target.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, object]] = []
    weekly_rows: list[object] = []
    for week in weeks:
        identity = _receipt_identity(
            week=week,
            environment=environment,
            development_prices=development_prices,
            methodology_version=methodology_version,
            runner=runner,
        )
        receipt = _receipt_path(target, identity)
        if resume and receipt.exists():
            result = _load_receipt(receipt, identity)
        else:
            result = runner(
                valuation_week=week,
                market="us",
                resume=resume,
                development_prices=development_prices,
                environment=environment,
                methodology_version=methodology_version,
                checkpoint_dir=target,
            )
            result = _json_result(result)
            if result.get("status") == "success":
                _write_receipt(receipt, identity, result)
        results.append(result)
        weekly_rows.extend(result.get("weekly_rows", ()))
        if result.get("status") != "success":
            return {
                "status": "failed",
                "weeks": [item.isoformat() for item in weeks],
                "completed_weeks": len(results) - 1,
                "failed_week": week.isoformat(),
                "failure_summary": result.get("failure_summary", "weekly backfill failed"),
                "weekly_rows": tuple(weekly_rows),
                "results": results,
            }
    return {
        "status": "success",
        "weeks": [week.isoformat() for week in weeks],
        "completed_weeks": len(results),
        "weekly_rows": tuple(weekly_rows),
        "results": results,
    }


def _date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("date must use YYYY-MM-DD") from exc


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a bounded US country-index backfill")
    parser.add_argument("--from", dest="from_date", type=_date, required=True)
    parser.add_argument("--to", dest="to_date", type=_date, required=True)
    parser.add_argument("--market", required=True, choices=("us",))
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--development-prices", action="store_true")
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    flow_runner: FlowRunner | None = None,
    checkpoint_dir: str | Path = ".mvd-checkpoints/backfill",
) -> int:
    parser = _parser()
    try:
        args = parser.parse_args(argv)
        result = run_backfill(
            args.from_date,
            args.to_date,
            market=args.market,
            resume=args.resume,
            development_prices=args.development_prices,
            environment="development" if args.development_prices else "production",
            checkpoint_dir=checkpoint_dir,
            flow_runner=flow_runner,
        )
    except (BackfillConfigurationError, SystemExit) as exc:
        if isinstance(exc, SystemExit):
            return int(exc.code)
        result = {"status": "failed", "failure_summary": str(exc)}
    print(json.dumps(result, indent=2, default=str))
    return 0 if result.get("status") == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
