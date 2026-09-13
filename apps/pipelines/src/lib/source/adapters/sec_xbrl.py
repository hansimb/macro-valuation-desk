from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from urllib.request import Request, urlopen

from src.lib.source.country_index_types import RawXbrlFact, RegulatoryFiling
from src.lib.source.types import SourceError


FetchJson = Callable[[str, Mapping[str, str]], Mapping[str, object]]


@dataclass(frozen=True)
class SecCompany:
    cik: str
    name: str
    ticker: str
    exchange: str


@dataclass(frozen=True)
class SecXbrlResult:
    ok: bool
    company: SecCompany | None = None
    filings: tuple[RegulatoryFiling, ...] = ()
    facts: tuple[RawXbrlFact, ...] = ()
    error: SourceError | None = None

    @classmethod
    def failure(
        cls,
        *,
        cik: str,
        url: str,
        error_type: str,
        message: str,
    ) -> "SecXbrlResult":
        return cls(
            ok=False,
            error=SourceError(
                provider="sec",
                key=cik,
                external_series_id=url,
                error_type=error_type,
                message=message,
            ),
        )


@dataclass(frozen=True)
class _FactCandidate:
    taxonomy: str
    concept_name: str
    unit: str
    observation: Mapping[str, object]
    accession: str
    filing_form: str
    filing_date: date
    accepted_at: datetime | None
    published_at: datetime
    period_start: date | None
    period_end: date | None
    instant_date: date | None
    context_id: str | None
    frame: str | None
    amendment_of_accession: str | None
    ordinal: int


class SecXbrlAdapter:
    """Acquire SEC company metadata and XBRL facts through an injectable transport.

    Incremental requests use the SEC companyfacts endpoint. Historical callers can
    use ``BULK_COMPANYFACTS_URL`` to obtain the SEC bulk archive before passing a
    company payload through the same parser.
    """

    COMPANY_TICKERS_EXCHANGE_URL = "https://www.sec.gov/files/company_tickers_exchange.json"
    BULK_COMPANYFACTS_URL = "https://www.sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip"
    USER_AGENT = "Macro Valuation Desk contact@macrovaluationdesk.com"
    SUPPORTED_FORMS = frozenset({"10-K", "10-Q", "20-F", "40-F"})

    def __init__(
        self,
        *,
        fetch_json: FetchJson | None = None,
        user_agent: str | None = None,
    ) -> None:
        self._fetch_json = fetch_json or _fetch_json
        self._user_agent = user_agent or self.USER_AGENT

    def discover_company(self, cik: str) -> SecXbrlResult:
        """Find an exchange-listed SEC registrant by its normalized CIK."""
        try:
            normalized_cik = _normalize_cik(cik)
        except ValueError as exc:
            return SecXbrlResult.failure(
                cik=str(cik),
                url=self.COMPANY_TICKERS_EXCHANGE_URL,
                error_type="validation_error",
                message=str(exc),
            )

        try:
            payload = self._fetch_json(self.COMPANY_TICKERS_EXCHANGE_URL, self._headers())
            company = _company_from_tickers(payload, normalized_cik)
        except (OSError, ValueError, TypeError, KeyError) as exc:
            return SecXbrlResult.failure(
                cik=normalized_cik,
                url=self.COMPANY_TICKERS_EXCHANGE_URL,
                error_type="fetch_error" if isinstance(exc, OSError) else "parse_error",
                message=str(exc),
            )

        if company is None:
            return SecXbrlResult.failure(
                cik=normalized_cik,
                url=self.COMPANY_TICKERS_EXCHANGE_URL,
                error_type="not_found",
                message=f"CIK {normalized_cik} is absent from SEC exchange ticker metadata.",
            )
        return SecXbrlResult(ok=True, company=company)

    def fetch_companyfacts(self, cik: str) -> SecXbrlResult:
        """Fetch supported SEC companyfacts and retain immutable filing lineage."""
        try:
            normalized_cik = _normalize_cik(cik)
        except ValueError as exc:
            return SecXbrlResult.failure(
                cik=str(cik),
                url=self.COMPANY_TICKERS_EXCHANGE_URL,
                error_type="validation_error",
                message=str(exc),
            )

        source_url = self.companyfacts_url(normalized_cik)
        try:
            payload = self._fetch_json(source_url, self._headers())
            fetched_at = datetime.now(timezone.utc)
        except OSError as exc:
            return SecXbrlResult.failure(
                cik=normalized_cik,
                url=source_url,
                error_type="fetch_error",
                message=str(exc),
            )
        except Exception as exc:
            return SecXbrlResult.failure(
                cik=normalized_cik,
                url=source_url,
                error_type="fetch_error",
                message=str(exc),
            )

        try:
            filings, facts = _parse_companyfacts(payload, normalized_cik, source_url, fetched_at)
        except (ValueError, TypeError, KeyError) as exc:
            return SecXbrlResult.failure(
                cik=normalized_cik,
                url=source_url,
                error_type="parse_error",
                message=str(exc),
            )

        return SecXbrlResult(ok=True, filings=filings, facts=facts)

    @staticmethod
    def companyfacts_url(cik: str) -> str:
        return f"https://data.sec.gov/api/xbrl/companyfacts/CIK{_normalize_cik(cik)}.json"

    def _headers(self) -> dict[str, str]:
        return {"Accept": "application/json", "User-Agent": self._user_agent}


def _fetch_json(url: str, headers: Mapping[str, str]) -> Mapping[str, object]:
    request = Request(url, headers=dict(headers))
    with urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"SEC returned a non-object JSON payload for {url}")
    return payload


def _normalize_cik(cik: str) -> str:
    value = str(cik).strip().upper()
    if value.startswith("CIK"):
        value = value[3:]
    if not value.isdigit() or not value:
        raise ValueError(f"CIK must contain only digits: {cik!r}")
    return f"{int(value):010d}"


def _company_from_tickers(payload: Mapping[str, object], cik: str) -> SecCompany | None:
    fields = payload.get("fields")
    rows = payload.get("data")
    if not isinstance(fields, list) or not isinstance(rows, list):
        raise ValueError("SEC ticker metadata must contain fields and data arrays")
    try:
        indexes = {str(field): index for index, field in enumerate(fields)}
        cik_index = indexes["cik"]
        name_index = indexes["name"]
        ticker_index = indexes["ticker"]
        exchange_index = indexes["exchange"]
    except KeyError as exc:
        raise ValueError(f"SEC ticker metadata is missing field {exc.args[0]!r}") from exc

    for row in rows:
        if not isinstance(row, list) or len(row) <= max(indexes.values()):
            raise ValueError("SEC ticker metadata contains a malformed row")
        if _normalize_cik(str(row[cik_index])) == cik:
            return SecCompany(
                cik=cik,
                name=str(row[name_index]),
                ticker=str(row[ticker_index]),
                exchange=str(row[exchange_index]),
            )
    return None


def _parse_companyfacts(
    payload: Mapping[str, object],
    expected_cik: str,
    source_url: str,
    fetched_at: datetime,
) -> tuple[tuple[RegulatoryFiling, ...], tuple[RawXbrlFact, ...]]:
    payload_cik = _normalize_cik(str(payload["cik"]))
    if payload_cik != expected_cik:
        raise ValueError(f"SEC companyfacts CIK {payload_cik} does not match requested {expected_cik}")
    entity_name = str(payload["entityName"])
    candidates = _fact_candidates(payload)
    amendment_links = _amendment_links(candidates)

    by_accession: dict[str, list[_FactCandidate]] = defaultdict(list)
    for candidate in candidates:
        by_accession[candidate.accession].append(candidate)

    filings_by_accession: dict[str, RegulatoryFiling] = {}
    for accession, filing_candidates in by_accession.items():
        representative = min(filing_candidates, key=lambda candidate: candidate.published_at)
        content_json = {
            "cik": payload_cik,
            "entityName": entity_name,
            "facts": [
                {
                    "taxonomy": candidate.taxonomy,
                    "concept": candidate.concept_name,
                    "unit": candidate.unit,
                    "value": dict(candidate.observation),
                }
                for candidate in filing_candidates
            ],
        }
        content_hash = _content_hash(content_json)
        filings_by_accession[accession] = RegulatoryFiling(
            provider="sec",
            external_id=accession,
            content_hash=content_hash,
            jurisdiction="US",
            filer_id=payload_cik,
            filing_form=representative.filing_form,
            document_url=source_url,
            content_json=content_json,
            fetched_at=fetched_at,
            filing_date=representative.filing_date,
            accepted_at=representative.accepted_at,
            published_at=representative.published_at,
            amendment_of_external_id=amendment_links.get(accession),
        )

    facts: list[RawXbrlFact] = []
    for candidate in candidates:
        filing = filings_by_accession[candidate.accession]
        amendment_of = candidate.amendment_of_accession or amendment_links.get(candidate.accession)
        facts.append(
            RawXbrlFact(
                filing_provider="sec",
                filing_id=candidate.accession,
                filing_content_hash=filing.content_hash,
                fact_id=(
                    f"{candidate.taxonomy}:{candidate.concept_name}:"
                    f"{candidate.accession}:{candidate.unit}:{candidate.ordinal}"
                ),
                taxonomy=candidate.taxonomy,
                concept_name=candidate.concept_name,
                value_text=str(candidate.observation["val"]),
                published_at=candidate.published_at,
                context_id=candidate.context_id,
                entity_id=payload_cik,
                dimensions=_dimensions(candidate.observation),
                unit=candidate.unit,
                decimals=_optional_text(candidate.observation.get("decimals")),
                period_start=candidate.period_start,
                period_end=candidate.period_end,
                instant_date=candidate.instant_date,
                filing_date=candidate.filing_date,
                filing_form=candidate.filing_form,
                frame=candidate.frame,
                source_url=source_url,
                amendment_of_filing_id=amendment_of,
                amended_at=candidate.published_at if amendment_of is not None else None,
            )
        )

    return (
        tuple(filings_by_accession[accession] for accession in sorted(filings_by_accession)),
        tuple(facts),
    )


def _fact_candidates(payload: Mapping[str, object]) -> list[_FactCandidate]:
    facts = payload.get("facts")
    if not isinstance(facts, Mapping):
        raise ValueError("SEC companyfacts payload is missing facts")

    candidates: list[_FactCandidate] = []
    ordinal = 0
    for taxonomy, concepts in facts.items():
        if not isinstance(concepts, Mapping):
            raise ValueError(f"SEC taxonomy {taxonomy!r} is not an object")
        for concept_name, concept in concepts.items():
            if not isinstance(concept, Mapping):
                raise ValueError(f"SEC concept {concept_name!r} is not an object")
            units = concept.get("units")
            if not isinstance(units, Mapping):
                raise ValueError(f"SEC concept {concept_name!r} is missing units")
            for unit, observations in units.items():
                if not isinstance(observations, list):
                    raise ValueError(f"SEC unit {unit!r} is not an array")
                for observation in observations:
                    if not isinstance(observation, Mapping):
                        raise ValueError("SEC fact observation is not an object")
                    filing_form = str(observation.get("form", ""))
                    if _base_form(filing_form) not in SecXbrlAdapter.SUPPORTED_FORMS:
                        continue
                    candidates.append(
                        _candidate(
                            taxonomy=str(taxonomy),
                            concept_name=str(concept_name),
                            unit=str(unit),
                            observation=observation,
                            ordinal=ordinal,
                        )
                    )
                    ordinal += 1
    return candidates


def _candidate(
    *,
    taxonomy: str,
    concept_name: str,
    unit: str,
    observation: Mapping[str, object],
    ordinal: int,
) -> _FactCandidate:
    accession = _required_text(observation, "accn")
    filing_form = _required_text(observation, "form")
    filing_date = _date_value(observation, "filed")
    published_at = _timestamp_value(observation.get("published"))
    accepted_at = _optional_timestamp(
        observation.get("accepted") or observation.get("acceptanceDateTime")
    )
    if published_at is None:
        published_at = accepted_at or datetime.combine(filing_date, time.min, tzinfo=timezone.utc)
    start = _optional_date(observation.get("start"))
    end = _optional_date(observation.get("end"))
    if end is None:
        raise ValueError(f"SEC fact {accession} is missing end date")
    return _FactCandidate(
        taxonomy=taxonomy,
        concept_name=concept_name,
        unit=unit,
        observation=observation,
        accession=accession,
        filing_form=filing_form,
        filing_date=filing_date,
        accepted_at=accepted_at,
        published_at=published_at,
        period_start=start,
        period_end=end if start is not None else None,
        instant_date=end if start is None else None,
        context_id=_optional_text(observation.get("context")),
        frame=_optional_text(observation.get("frame")),
        amendment_of_accession=_optional_text(observation.get("amendmentOf")),
        ordinal=ordinal,
    )


def _amendment_links(candidates: list[_FactCandidate]) -> dict[str, str]:
    links: dict[str, str] = {}
    ordered = sorted(candidates, key=lambda candidate: candidate.published_at)
    for candidate in ordered:
        if candidate.amendment_of_accession is not None:
            links[candidate.accession] = candidate.amendment_of_accession
            continue
        if not candidate.filing_form.endswith("/A") or candidate.accession in links:
            continue
        matches = [
            earlier
            for earlier in ordered
            if earlier.published_at < candidate.published_at
            and not earlier.filing_form.endswith("/A")
            and earlier.taxonomy == candidate.taxonomy
            and earlier.concept_name == candidate.concept_name
            and earlier.unit == candidate.unit
            and earlier.period_start == candidate.period_start
            and earlier.period_end == candidate.period_end
            and earlier.instant_date == candidate.instant_date
            and _base_form(earlier.filing_form) == _base_form(candidate.filing_form)
        ]
        if matches:
            links[candidate.accession] = matches[-1].accession
    return links


def _content_hash(content: Mapping[str, object]) -> str:
    encoded = json.dumps(content, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _base_form(filing_form: str) -> str:
    return filing_form.partition("/")[0]


def _required_text(value: Mapping[str, object], key: str) -> str:
    result = _optional_text(value.get(key))
    if result is None:
        raise ValueError(f"SEC fact is missing {key}")
    return result


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    result = str(value)
    return result if result else None


def _date_value(value: Mapping[str, object], key: str) -> date:
    parsed = _optional_date(value.get(key))
    if parsed is None:
        raise ValueError(f"SEC fact is missing {key}")
    return parsed


def _optional_date(value: object) -> date | None:
    text = _optional_text(value)
    return date.fromisoformat(text) if text is not None else None


def _timestamp_value(value: object) -> datetime | None:
    return _optional_timestamp(value)


def _optional_timestamp(value: object) -> datetime | None:
    text = _optional_text(value)
    if text is None:
        return None
    parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("SEC timestamp must include a timezone offset")
    return parsed


def _dimensions(observation: Mapping[str, object]) -> Mapping[str, object]:
    dimensions = observation.get("dimensions", {})
    if not isinstance(dimensions, Mapping):
        raise ValueError("SEC fact dimensions must be an object")
    return dimensions
