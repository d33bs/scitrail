"""Tests for fallback summarizer behavior."""

from __future__ import annotations

from scitrail.models import VoiceCandidate, WorkSnippet
from scitrail.summarizer import FallbackSummarizer


def test_fallback_person_summary() -> None:
    """Fallback summarizer should produce deterministic topic summary."""

    candidate = VoiceCandidate(
        author_id="A1",
        display_name="Alice",
        orcid="https://orcid.org/0000-0001",
        works=[
            WorkSnippet(id="W1", title="Paper A", concepts=["Quantum", "Optimization"]),
            WorkSnippet(id="W2", title="Paper B", concepts=["Quantum", "Learning"]),
        ],
    )

    summarizer = FallbackSummarizer()
    summary = summarizer.summarize_person(candidate=candidate, topic="Quantum")

    assert summary.person_name == "Alice"
    assert summary.key_topics[0] == "Quantum"
    assert "Quantum" in summary.state_of_work
