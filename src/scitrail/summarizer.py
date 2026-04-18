"""Summarization backends for voice and executive summaries."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import Counter
from importlib import import_module
from urllib.request import urlretrieve

from pydantic import BaseModel

from scitrail.models import (
    EvidenceWork,
    ExecutiveSummary,
    LLMSettings,
    PersonSummary,
    VoiceCandidate,
)


class _PersonSummaryResponse(BaseModel):
    """Response schema for person-level LLM summaries."""

    state_of_work: str
    key_topics: list[str]


class _ExecutiveSummaryResponse(BaseModel):
    """Response schema for executive LLM summaries."""

    state_of_art: str
    trends: list[str]
    open_questions: list[str]


class BaseSummarizer(ABC):
    """Base class for summary generation backends."""

    @abstractmethod
    def summarize_person(self, candidate: VoiceCandidate, topic: str) -> PersonSummary:
        """Create a summary for a single top voice."""

    @abstractmethod
    def summarize_executive(
        self,
        *,
        person_summaries: list[PersonSummary],
        topic: str,
        institution_name: str,
    ) -> ExecutiveSummary:
        """Create an executive summary over all top voices."""


class FallbackSummarizer(BaseSummarizer):
    """Deterministic summarizer used when local LLM setup is unavailable."""

    def summarize_person(self, candidate: VoiceCandidate, topic: str) -> PersonSummary:
        """Create a lightweight person summary from concept/title frequency."""

        concept_counts: Counter[str] = Counter()
        for work in candidate.works:
            concept_counts.update(work.concepts)

        key_topics = [name for name, _ in concept_counts.most_common(5)]
        evidence_works = [
            EvidenceWork(title=work.title, work_id=work.id, doi=work.doi)
            for work in candidate.works[:5]
        ]
        state_of_work = (
            f"{candidate.display_name} is a recurring contributor in {topic}. "
            f"Across {len(candidate.works)} high-signal works, their publications "
            "focus on the themes listed below."
        )

        return PersonSummary(
            person_name=candidate.display_name,
            orcid=candidate.orcid,
            state_of_work=state_of_work,
            key_topics=key_topics,
            evidence_works=evidence_works,
        )

    def summarize_executive(
        self,
        *,
        person_summaries: list[PersonSummary],
        topic: str,
        institution_name: str,
    ) -> ExecutiveSummary:
        """Create a deterministic executive summary from person summaries."""

        all_topics: Counter[str] = Counter()
        for summary in person_summaries:
            all_topics.update(summary.key_topics)

        trends = [topic_name for topic_name, _ in all_topics.most_common(5)]
        trend_sentence = (
            ", ".join(trends) if trends else "emerging multidisciplinary themes"
        )

        state_of_art = (
            f"At {institution_name}, current work in {topic} is shaped by "
            f"{len(person_summaries)} "
            f"recurring voices, with concentration around {trend_sentence}."
        )

        open_questions = [
            "Which subtopics are underrepresented in highly cited publications?",
            "Where are opportunities for cross-team collaboration based on "
            "shared themes?",
        ]

        return ExecutiveSummary(
            state_of_art=state_of_art,
            trends=trends,
            open_questions=open_questions,
        )


class LocalInstructorSummarizer(FallbackSummarizer):
    """LLM summarizer using instructor with a local llama-cpp model."""

    def __init__(self, llm_settings: LLMSettings) -> None:
        """Load local model and prepare instructor-compatible client."""
        instructor = import_module("instructor")
        llama_cpp_module = import_module("llama_cpp")
        Llama = llama_cpp_module.Llama

        model_url = (
            f"https://huggingface.co/{llm_settings.model_repo_id}/resolve/main/"
            f"{llm_settings.model_filename}?download=true"
        )
        cache_dir = llm_settings.expanded_cache_dir
        cache_dir.mkdir(parents=True, exist_ok=True)
        model_path = cache_dir / llm_settings.model_filename
        if not model_path.exists():
            urlretrieve(model_url, model_path)

        llm = Llama(
            model_path=str(model_path),
            n_ctx=llm_settings.model_context_size,
            verbose=False,
        )
        self._temperature = llm_settings.temperature
        self._create = instructor.patch(
            create=llm.create_chat_completion_openai_v1,
            mode=instructor.Mode.MD_JSON,
        )

    def summarize_person(self, candidate: VoiceCandidate, topic: str) -> PersonSummary:
        """Use local model for structured summary of a top voice."""

        works_text = "\n".join(
            f"- {work.title} | concepts: {', '.join(work.concepts[:5])}"
            for work in candidate.works[:8]
        )
        prompt = (
            "Summarize this researcher's current contributions in a field. "
            "Return concise, factual prose and topic phrases only from evidence.\n"
            f"Field: {topic}\n"
            f"Person: {candidate.display_name}\n"
            f"Evidence:\n{works_text}"
        )

        response = self._create(
            response_model=_PersonSummaryResponse,
            messages=[{"role": "user", "content": prompt}],
            temperature=self._temperature,
        )

        return PersonSummary(
            person_name=candidate.display_name,
            orcid=candidate.orcid,
            state_of_work=response.state_of_work,
            key_topics=response.key_topics,
            evidence_works=[
                EvidenceWork(title=work.title, work_id=work.id, doi=work.doi)
                for work in candidate.works[:5]
            ],
        )

    def summarize_executive(
        self,
        *,
        person_summaries: list[PersonSummary],
        topic: str,
        institution_name: str,
    ) -> ExecutiveSummary:
        """Use local model for an executive state-of-the-art synthesis."""

        people_text = "\n".join(
            f"- {summary.person_name}: {summary.state_of_work}; "
            f"topics={', '.join(summary.key_topics[:5])}"
            for summary in person_summaries
        )
        prompt = (
            "Create an executive summary for the current state of a research field. "
            "Be concise and avoid hype.\n"
            f"Institution: {institution_name}\n"
            f"Field: {topic}\n"
            f"Evidence:\n{people_text}"
        )

        response = self._create(
            response_model=_ExecutiveSummaryResponse,
            messages=[{"role": "user", "content": prompt}],
            temperature=self._temperature,
        )

        return ExecutiveSummary(
            state_of_art=response.state_of_art,
            trends=response.trends,
            open_questions=response.open_questions,
        )


def build_summarizer(settings: LLMSettings) -> BaseSummarizer:
    """Build a local-LLM summarizer when enabled and available, else fallback."""

    if not settings.enabled:
        return FallbackSummarizer()

    try:
        return LocalInstructorSummarizer(settings=settings)
    except Exception:
        return FallbackSummarizer()
