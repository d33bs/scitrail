"""Domain and configuration models for scitrail."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field, computed_field, model_validator


class LLMSettings(BaseModel):
    """Settings for local-first LLM summarization."""

    enabled: bool = True
    model_repo_id: str = "hugging-quants/Llama-3.2-3B-Instruct-Q4_K_M-GGUF"
    model_filename: str = "llama-3.2-3b-instruct-q4_k_m.gguf"
    model_context_size: int = 32768
    model_cache_dir: str = "~/.cache/scitrail"
    temperature: float = 0.0

    @computed_field
    @property
    def expanded_cache_dir(self) -> Path:
        """Return model cache directory with user home expanded."""

        return Path(self.model_cache_dir).expanduser()


class ReportConfig(BaseModel):
    """User-defined report configuration loaded from YAML."""

    institution: str
    department: str | None = None
    departments: list[str] | None = None
    topic: str | None = None
    topics: list[str] | None = None
    max_people: int = Field(default=5, ge=1, le=25)
    works_per_person: int = Field(default=8, ge=1, le=50)
    lookback_years: int = Field(default=5, ge=1, le=30)
    require_orcid: bool = True
    disambiguate_names_with_llm: bool = True
    require_all_topics: bool = True
    openalex_email: str | None = None
    openalex_api_key: str | None = None
    llm: LLMSettings = Field(default_factory=LLMSettings)

    @model_validator(mode="after")
    def validate_topic_inputs(self) -> "ReportConfig":
        """Ensure at least one topic is configured."""

        if not self.active_topics:
            msg = "Provide at least one topic via `topic` or `topics`."
            raise ValueError(msg)
        return self

    @computed_field
    @property
    def active_topics(self) -> list[str]:
        """Return normalized list of topics from single or multi-value inputs."""

        values: list[str] = []
        if self.topic:
            values.append(self.topic)
        if self.topics:
            values.extend(self.topics)
        return _normalized_unique(values)

    @computed_field
    @property
    def active_departments(self) -> list[str]:
        """Return normalized list of departments from single or multi-value inputs."""

        values: list[str] = []
        if self.department:
            values.append(self.department)
        if self.departments:
            values.extend(self.departments)
        return _normalized_unique(values)


class InstitutionRecord(BaseModel):
    """Resolved institution metadata from OpenAlex."""

    id: str
    display_name: str
    ror: str | None = None


class WorkSnippet(BaseModel):
    """Minimal work payload needed for analysis."""

    id: str
    title: str
    publication_year: int | None = None
    doi: str | None = None
    cited_by_count: int = 0
    concepts: list[str] = Field(default_factory=list)
    topic_signals: list[str] = Field(default_factory=list)
    abstract: str | None = None


class VoiceCandidate(BaseModel):
    """Aggregated evidence for a potential top voice."""

    author_id: str
    display_name: str
    orcid: str | None = None
    alias_names: list[str] = Field(default_factory=list)
    works: list[WorkSnippet] = Field(default_factory=list)
    total_citations: int = 0


class EvidenceWork(BaseModel):
    """Evidence work reference used in report output."""

    title: str
    work_id: str
    doi: str | None = None
    topic_signals: list[str] = Field(default_factory=list)


class PersonSummary(BaseModel):
    """Structured summary per top voice."""

    person_name: str
    orcid: str | None = None
    state_of_work: str
    key_topics: list[str] = Field(default_factory=list)
    evidence_works: list[EvidenceWork] = Field(default_factory=list)


class ExecutiveSummary(BaseModel):
    """Structured state-of-the-art summary."""

    state_of_art: str
    trends: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)


class ReportData(BaseModel):
    """Final data object used to render markdown."""

    config: ReportConfig
    institution: InstitutionRecord
    top_voices: list[PersonSummary]
    executive_summary: ExecutiveSummary


def _normalized_unique(values: list[str]) -> list[str]:
    """Normalize strings and return a stable unique list."""

    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        stripped = value.strip()
        if not stripped:
            continue
        lowered = stripped.casefold()
        if lowered in seen:
            continue
        seen.add(lowered)
        normalized.append(stripped)
    return normalized
