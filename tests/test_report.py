"""Tests for markdown rendering."""

from __future__ import annotations

from scitrail.models import (
    EvidenceWork,
    ExecutiveSummary,
    InstitutionRecord,
    PersonSummary,
    ReportConfig,
    ReportData,
)
from scitrail.report import render_markdown


def test_render_markdown_sections() -> None:
    """Rendered report should include core sections and fields."""

    data = ReportData(
        config=ReportConfig(
            institution="CU Anschutz",
            department="Department of Biomedical Informatics",
            topic="Quantum",
        ),
        institution=InstitutionRecord(
            id="https://openalex.org/I123",
            display_name="CU Anschutz",
            ror="04x9a0q46",
        ),
        top_voices=[
            PersonSummary(
                person_name="Alice",
                orcid="https://orcid.org/0000-0001",
                state_of_work="Focuses on quantum optimization.",
                key_topics=["Quantum", "Optimization"],
                evidence_works=[
                    EvidenceWork(
                        title="Paper A",
                        work_id="https://openalex.org/W1",
                        doi="10.1000/test-doi",
                    )
                ],
            )
        ],
        executive_summary=ExecutiveSummary(
            state_of_art="The field is converging on quantum optimization.",
            trends=["Quantum optimization"],
            open_questions=["How robust are current methods?"],
        ),
    )

    markdown = render_markdown(data)

    assert "# SciTrail Report: Quantum" in markdown
    assert "Department: **Department of Biomedical Informatics**" in markdown
    assert "## Executive Summary" in markdown
    assert "## Top Voices" in markdown
    assert "Alice" in markdown
    assert "https://orcid.org/0000-0001" in markdown
    assert "[Paper A](https://doi.org/10.1000/test-doi)" in markdown
