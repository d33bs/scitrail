"""Tests for report generation pipeline."""

from __future__ import annotations

from pathlib import Path

from scitrail.models import (
    EvidenceWork,
    ExecutiveSummary,
    InstitutionRecord,
    PersonSummary,
    ReportConfig,
    VoiceCandidate,
    WorkSnippet,
)
from scitrail.pipeline import generate_report_file, generate_report_markdown


class _FakeOpenAlexClient:
    def __init__(self, settings: ReportConfig) -> None:
        self.settings = settings

    def resolve_institution(self, institution_query: str) -> InstitutionRecord:
        assert institution_query == "CU Anschutz"
        return InstitutionRecord(
            id="https://openalex.org/I123",
            display_name="CU Anschutz",
            ror="04x9a0q46",
        )

    def fetch_topic_works(
        self,
        *,
        topic: str,
        institution: InstitutionRecord,
        lookback_years: int,
        max_records: int,
    ) -> list[dict[str, object]]:
        assert topic == "Quantum"
        assert institution.display_name == "CU Anschutz"
        assert lookback_years == 5
        assert max_records >= 50
        return [{"id": "W1"}]


class _FakeSummarizer:
    def summarize_person(self, candidate: VoiceCandidate, topic: str) -> PersonSummary:
        assert topic == "Quantum"
        return PersonSummary(
            person_name=candidate.display_name,
            orcid=candidate.orcid,
            state_of_work="summary",
            key_topics=["Quantum"],
            evidence_works=[
                EvidenceWork(title=work.title, work_id=work.id)
                for work in candidate.works
            ],
        )

    def summarize_executive(
        self,
        *,
        person_summaries: list[PersonSummary],
        topic: str,
        institution_name: str,
    ) -> ExecutiveSummary:
        assert topic == "Quantum"
        assert institution_name == "CU Anschutz"
        assert len(person_summaries) == 1
        return ExecutiveSummary(
            state_of_art="state",
            trends=["Quantum"],
            open_questions=["question"],
        )


def test_generate_report_markdown(monkeypatch, sample_config_path: Path) -> None:
    """Pipeline should generate markdown text from mocked dependencies."""

    monkeypatch.setattr("scitrail.pipeline.OpenAlexClient", _FakeOpenAlexClient)

    observed_department: dict[str, str | None] = {"value": None}

    def fake_extract_top_voices(**kwargs):
        observed_department["value"] = kwargs["department"]
        return [
            VoiceCandidate(
                author_id="A1",
                display_name="Alice",
                orcid="https://orcid.org/0000-0001",
                works=[WorkSnippet(id="W1", title="Paper A")],
            )
        ]

    monkeypatch.setattr("scitrail.pipeline.extract_top_voices", fake_extract_top_voices)
    monkeypatch.setattr(
        "scitrail.pipeline.build_summarizer", lambda _: _FakeSummarizer()
    )

    markdown = generate_report_markdown(sample_config_path)

    assert observed_department["value"] == "Department of Biomedical Informatics"
    assert "# SciTrail Report: Quantum" in markdown
    assert "Department: **Department of Biomedical Informatics**" in markdown
    assert "Alice" in markdown
    assert "state" in markdown


def test_generate_report_file(
    monkeypatch, sample_config_path: Path, tmp_path: Path
) -> None:
    """Pipeline file writer should persist generated markdown."""

    monkeypatch.setattr(
        "scitrail.pipeline.generate_report_markdown",
        lambda config_path: "# Report\n",
    )

    destination = tmp_path / "report.md"
    output = generate_report_file(sample_config_path, destination)

    assert output == destination
    assert destination.read_text(encoding="utf-8") == "# Report\n"
