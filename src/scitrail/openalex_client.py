"""OpenAlex data access helpers built on top of pyalex."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime

from pyalex import Institutions, Works
from pyalex import config as pyalex_config

from scitrail.models import InstitutionRecord, ReportConfig, VoiceCandidate, WorkSnippet

MIN_TOPIC_TERM_LENGTH = 3


@dataclass(frozen=True)
class VoiceExtractionOptions:
    """Options controlling top-voice extraction behavior."""

    departments: list[str] | None
    topics: list[str]
    max_people: int
    works_per_person: int
    strict_topic_match: bool = True


class OpenAlexClient:
    """Small wrapper around pyalex calls used by the report pipeline."""

    def __init__(self, settings: ReportConfig) -> None:
        """Initialize client and apply OpenAlex auth configuration."""

        if settings.openalex_email:
            pyalex_config.email = settings.openalex_email
        if settings.openalex_api_key:
            pyalex_config.api_key = settings.openalex_api_key

    def resolve_institution(self, institution_query: str) -> InstitutionRecord:
        """Resolve best matching institution, preferring records with ROR."""

        matches = Institutions().search(institution_query).get(per_page=10)
        if not matches:
            msg = f"No institution found for query: {institution_query}"
            raise ValueError(msg)

        lowered_query = institution_query.casefold()

        def _score(item: dict[str, object]) -> tuple[int, int]:
            name = str(item.get("display_name", "")).casefold()
            exact = 1 if name == lowered_query else 0
            has_ror = 1 if item.get("ror") else 0
            return (exact, has_ror)

        best = sorted(matches, key=_score, reverse=True)[0]
        return InstitutionRecord(
            id=str(best["id"]),
            display_name=str(best["display_name"]),
            ror=str(best["ror"]) if best.get("ror") else None,
        )

    def fetch_topic_works(
        self,
        *,
        topic: str,
        institution: InstitutionRecord,
        lookback_years: int,
        max_records: int,
    ) -> list[dict[str, object]]:
        """Fetch works matching topic and institution with most-cited first."""

        current_year = datetime.now(tz=UTC).year
        min_year = current_year - lookback_years
        query = Works().search(topic).filter(publication_year=f">{min_year}")
        if institution.ror:
            query = query.filter(authorships={"institutions": {"ror": institution.ror}})
        else:
            openalex_id = institution.id.rsplit("/", maxsplit=1)[-1]
            query = query.filter(authorships={"institutions": {"id": openalex_id}})

        return query.sort(cited_by_count="desc").get(per_page=max_records)


def _topic_terms(topics: list[str]) -> list[str]:
    """Split a topic string into lowercase terms for relevance checks."""
    terms: list[str] = []
    for topic in topics:
        terms.extend(re.findall(r"[a-z0-9]+", topic.casefold()))
    unique_terms: list[str] = []
    seen: set[str] = set()
    for term in terms:
        if len(term) < MIN_TOPIC_TERM_LENGTH:
            continue
        if term in seen:
            continue
        seen.add(term)
        unique_terms.append(term)
    return unique_terms


def _append_term_matches(
    *,
    signals: list[str],
    source_label: str,
    text: str,
    topic_terms: list[str],
) -> None:
    """Append matches from topic terms found in a given text."""

    text_lower = text.casefold()
    for term in topic_terms:
        if term in text_lower:
            signals.append(f"{source_label}:{term}")


def _append_concept_matches(
    *,
    signals: list[str],
    concepts: list[object],
    topic_terms: list[str],
) -> None:
    """Append concept-level matches for topic terms."""

    for concept in concepts:
        if not isinstance(concept, dict):
            continue
        concept_name = str(concept.get("display_name", ""))
        if not concept_name:
            continue
        concept_name_lower = concept_name.casefold()
        for term in topic_terms:
            if term in concept_name_lower:
                signals.append(f"concept:{concept_name}")


def _extract_topic_signals(
    work: dict[str, object], topic_terms: list[str]
) -> list[str]:
    """Extract simple topic-match evidence from title/concepts/abstract."""

    if not topic_terms:
        return []

    signals: list[str] = []
    title = str(work.get("display_name", ""))
    _append_term_matches(
        signals=signals,
        source_label="title",
        text=title,
        topic_terms=topic_terms,
    )

    concepts = work.get("concepts", [])
    if isinstance(concepts, list):
        _append_concept_matches(
            signals=signals,
            concepts=concepts,
            topic_terms=topic_terms,
        )

    abstract = work.get("abstract")
    if isinstance(abstract, str):
        _append_term_matches(
            signals=signals,
            source_label="abstract",
            text=abstract,
            topic_terms=topic_terms,
        )

    deduped = list(dict.fromkeys(signals))
    return deduped[:8]


def _build_work_snippet(
    work: dict[str, object], topic_signals: list[str]
) -> WorkSnippet:
    """Build a typed work snippet from a raw OpenAlex work object."""

    return WorkSnippet(
        id=str(work.get("id", "")),
        title=str(work.get("display_name", "Untitled")),
        publication_year=work.get("publication_year")
        if isinstance(work.get("publication_year"), int)
        else None,
        doi=work.get("doi") if isinstance(work.get("doi"), str) else None,
        cited_by_count=int(work.get("cited_by_count", 0) or 0),
        concepts=[
            str(concept.get("display_name"))
            for concept in work.get("concepts", [])
            if isinstance(concept, dict) and concept.get("display_name")
        ],
        topic_signals=topic_signals,
        abstract=(
            work.get("abstract") if isinstance(work.get("abstract"), str) else None
        ),
    )


def _authorship_matches_institution(
    authorship: dict[str, object],
    institution: InstitutionRecord,
    inst_id_short: str,
) -> bool:
    """Check if authorship includes the target institution."""

    institutions = authorship.get("institutions")
    if not isinstance(institutions, list):
        return False

    return any(
        isinstance(inst, dict)
        and (
            inst.get("ror") == institution.ror
            or str(inst.get("id", "")).endswith(inst_id_short)
        )
        for inst in institutions
    )


def _authorship_matches_departments(
    authorship: dict[str, object],
    *,
    departments: list[str] | None,
) -> bool:
    """Check if authorship affiliation metadata contains the department text."""

    if not departments:
        return True

    department_terms = [department.casefold() for department in departments]
    values: list[str] = []

    raw_affiliation_string = authorship.get("raw_affiliation_string")
    if isinstance(raw_affiliation_string, str):
        values.append(raw_affiliation_string)

    raw_affiliation_strings = authorship.get("raw_affiliation_strings")
    if isinstance(raw_affiliation_strings, list):
        values.extend(
            value for value in raw_affiliation_strings if isinstance(value, str)
        )

    institutions = authorship.get("institutions")
    if isinstance(institutions, list):
        values.extend(
            str(inst.get("display_name"))
            for inst in institutions
            if isinstance(inst, dict) and inst.get("display_name")
        )

    return any(
        term in value.casefold() for term in department_terms for value in values
    )


def _upsert_candidate(
    *,
    candidates: dict[str, VoiceCandidate],
    authorship: dict[str, object],
    work_item: WorkSnippet,
    works_per_person: int,
) -> None:
    """Create or update a voice candidate from an authorship entry."""

    author_obj = authorship.get("author")
    if not isinstance(author_obj, dict):
        return

    author_id = str(author_obj.get("id", "")).strip()
    if not author_id:
        return

    candidate = candidates.get(author_id)
    if candidate is None:
        candidate = VoiceCandidate(
            author_id=author_id,
            display_name=str(author_obj.get("display_name", "Unknown")),
            orcid=author_obj.get("orcid")
            if isinstance(author_obj.get("orcid"), str)
            else None,
        )
        candidates[author_id] = candidate

    if len(candidate.works) < works_per_person:
        candidate.works.append(work_item)
    candidate.total_citations += work_item.cited_by_count


def extract_top_voices(
    *,
    works: Iterable[dict[str, object]],
    institution: InstitutionRecord,
    options: VoiceExtractionOptions,
) -> list[VoiceCandidate]:
    """Extract and rank top voices from works by institutional authorship evidence."""

    candidates: dict[str, VoiceCandidate] = {}
    inst_id_short = institution.id.rsplit("/", maxsplit=1)[-1]
    topic_terms = _topic_terms(options.topics)

    for work in works:
        authorships = work.get("authorships")
        if not isinstance(authorships, list):
            continue

        topic_signals = _extract_topic_signals(work, topic_terms)
        if options.strict_topic_match and topic_terms and not topic_signals:
            continue

        work_item = _build_work_snippet(work, topic_signals=topic_signals)

        for authorship in authorships:
            if not isinstance(authorship, dict):
                continue
            if not _authorship_matches_institution(
                authorship=authorship,
                institution=institution,
                inst_id_short=inst_id_short,
            ):
                continue
            if not _authorship_matches_departments(
                authorship=authorship,
                departments=options.departments,
            ):
                continue

            _upsert_candidate(
                candidates=candidates,
                authorship=authorship,
                work_item=work_item,
                works_per_person=options.works_per_person,
            )

    sorted_candidates = sorted(
        candidates.values(),
        key=lambda candidate: (
            len(candidate.works),
            candidate.total_citations,
        ),
        reverse=True,
    )
    return sorted_candidates[: options.max_people]
