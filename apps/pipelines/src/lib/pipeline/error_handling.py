from __future__ import annotations

from src.lib.source.types import FetchResult


def collect_fetch_errors(fetch_results: list[FetchResult]) -> list[str]:
    return [
        f"{result.error.key}: {result.error.message}"
        for result in fetch_results
        if not result.ok and result.error is not None
    ]


def format_flow_errors(name: str, errors: list[object]) -> str:
    bullet_lines = "\n".join(f"  - {error}" for error in errors)
    return f"{name} flow failed:\n{bullet_lines}"


def raise_on_failed_flow(name: str, result: dict[str, object]) -> None:
    if result.get("status") != "failed":
        return

    errors = result.get("errors")
    if isinstance(errors, list):
        raise RuntimeError(format_flow_errors(name, errors))

    raise RuntimeError(f"{name} flow failed")
