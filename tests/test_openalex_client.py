"""Tests for OpenAlex extraction helpers."""

from __future__ import annotations

from scitrail.models import InstitutionRecord
from scitrail.openalex_client import VoiceExtractionOptions, extract_top_voices

INSTITUTION = InstitutionRecord(
    id="https://openalex.org/I123",
    display_name="CU Anschutz",
    ror="04x9a0q46",
)


def test_extract_top_voices_filters_and_ranks() -> None:
    """Should keep institution-matching authors and rank by evidence."""

    works = [
        {
            "id": "https://openalex.org/W1",
            "display_name": "Quantum paper one",
            "publication_year": 2024,
            "cited_by_count": 10,
            "concepts": [{"display_name": "Quantum computing"}],
            "authorships": [
                {
                    "author": {
                        "id": "https://openalex.org/A1",
                        "display_name": "Alice",
                        "orcid": "https://orcid.org/0000-0001",
                    },
                    "institutions": [
                        {
                            "id": "https://openalex.org/I123",
                            "ror": "04x9a0q46",
                            "display_name": "University of Colorado Anschutz",
                        }
                    ],
                },
                {
                    "author": {"id": "https://openalex.org/A2", "display_name": "Bob"},
                    "institutions": [
                        {"id": "https://openalex.org/I999", "ror": "other"}
                    ],
                },
            ],
        },
        {
            "id": "https://openalex.org/W2",
            "display_name": "Quantum paper two",
            "publication_year": 2025,
            "cited_by_count": 20,
            "concepts": [{"display_name": "Optimization"}],
            "authorships": [
                {
                    "author": {
                        "id": "https://openalex.org/A1",
                        "display_name": "Alice",
                        "orcid": "https://orcid.org/0000-0001",
                    },
                    "institutions": [
                        {
                            "id": "https://openalex.org/I123",
                            "ror": "04x9a0q46",
                            "display_name": "University of Colorado Anschutz",
                        }
                    ],
                },
                {
                    "author": {
                        "id": "https://openalex.org/A3",
                        "display_name": "Cara",
                        "orcid": None,
                    },
                    "institutions": [
                        {
                            "id": "https://openalex.org/I123",
                            "ror": "04x9a0q46",
                            "display_name": "University of Colorado Anschutz",
                        }
                    ],
                },
            ],
        },
    ]

    voices = extract_top_voices(
        works=works,
        institution=INSTITUTION,
        options=VoiceExtractionOptions(
            departments=None,
            topics=["Quantum"],
            max_people=2,
            works_per_person=5,
            require_orcid=False,
        ),
    )

    assert len(voices) == 2
    assert voices[0].display_name == "Alice"
    assert voices[0].total_citations == 30
    assert voices[1].display_name == "Cara"


def test_extract_top_voices_department_filter() -> None:
    """Should keep only authorships with matching department text."""

    works = [
        {
            "id": "https://openalex.org/W1",
            "display_name": "DBMI Quantum Paper",
            "cited_by_count": 12,
            "authorships": [
                {
                    "author": {
                        "id": "https://openalex.org/A1",
                        "display_name": "Alice",
                        "orcid": "https://orcid.org/0000-0001",
                    },
                    "raw_affiliation_string": (
                        "Department of Biomedical Informatics, "
                        "University of Colorado Anschutz Medical Campus"
                    ),
                    "institutions": [
                        {
                            "id": "https://openalex.org/I123",
                            "ror": "04x9a0q46",
                            "display_name": "University of Colorado Anschutz",
                        }
                    ],
                },
                {
                    "author": {
                        "id": "https://openalex.org/A9",
                        "display_name": "Outside",
                    },
                    "raw_affiliation_string": "Department of Physics, Other School",
                    "institutions": [
                        {
                            "id": "https://openalex.org/I123",
                            "ror": "04x9a0q46",
                            "display_name": "University of Colorado Anschutz",
                        }
                    ],
                },
            ],
        }
    ]

    voices = extract_top_voices(
        works=works,
        institution=INSTITUTION,
        options=VoiceExtractionOptions(
            departments=["Biomedical Informatics"],
            topics=["Quantum"],
            max_people=5,
            works_per_person=5,
        ),
    )

    assert len(voices) == 1
    assert voices[0].display_name == "Alice"


def test_extract_top_voices_requires_orcid_and_deduplicates() -> None:
    """Should require ORCID and merge records sharing the same ORCID."""

    works = [
        {
            "id": "https://openalex.org/W1",
            "display_name": "Quantum methods",
            "cited_by_count": 10,
            "concepts": [{"display_name": "Quantum computing"}],
            "authorships": [
                {
                    "author": {
                        "id": "https://openalex.org/A1",
                        "display_name": "Alice Smith",
                        "orcid": "https://orcid.org/0000-0001",
                    },
                    "institutions": [
                        {"id": "https://openalex.org/I123", "ror": "04x9a0q46"}
                    ],
                }
            ],
        },
        {
            "id": "https://openalex.org/W2",
            "display_name": "Quantum systems",
            "cited_by_count": 20,
            "concepts": [{"display_name": "Quantum"}],
            "authorships": [
                {
                    "author": {
                        "id": "https://openalex.org/A2",
                        "display_name": "A. Smith",
                        "orcid": "https://orcid.org/0000-0001",
                    },
                    "institutions": [
                        {"id": "https://openalex.org/I123", "ror": "04x9a0q46"}
                    ],
                },
                {
                    "author": {
                        "id": "https://openalex.org/A3",
                        "display_name": "No Orcid Person",
                        "orcid": None,
                    },
                    "institutions": [
                        {"id": "https://openalex.org/I123", "ror": "04x9a0q46"}
                    ],
                },
            ],
        },
    ]

    voices = extract_top_voices(
        works=works,
        institution=INSTITUTION,
        options=VoiceExtractionOptions(
            departments=None,
            topics=["Quantum"],
            max_people=5,
            works_per_person=5,
            require_orcid=True,
        ),
    )

    assert len(voices) == 1
    assert voices[0].orcid == "https://orcid.org/0000-0001"
    assert len(voices[0].works) == 2


def test_extract_top_voices_multi_topic_and_matching() -> None:
    """Works should match all configured topics when require_all_topics is true."""

    works = [
        {
            "id": "https://openalex.org/W1",
            "display_name": "Quantum advances",
            "cited_by_count": 5,
            "concepts": [{"display_name": "Quantum computing"}],
            "authorships": [
                {
                    "author": {
                        "id": "https://openalex.org/A1",
                        "display_name": "Alice",
                        "orcid": "https://orcid.org/0000-0001",
                    },
                    "institutions": [
                        {"id": "https://openalex.org/I123", "ror": "04x9a0q46"}
                    ],
                }
            ],
        },
        {
            "id": "https://openalex.org/W2",
            "display_name": "Quantum bioinformatics methods",
            "cited_by_count": 9,
            "concepts": [{"display_name": "Bioinformatics"}],
            "authorships": [
                {
                    "author": {
                        "id": "https://openalex.org/A1",
                        "display_name": "Alice",
                        "orcid": "https://orcid.org/0000-0001",
                    },
                    "institutions": [
                        {"id": "https://openalex.org/I123", "ror": "04x9a0q46"}
                    ],
                }
            ],
        },
    ]

    voices = extract_top_voices(
        works=works,
        institution=INSTITUTION,
        options=VoiceExtractionOptions(
            departments=None,
            topics=["Quantum", "Bioinformatics"],
            max_people=5,
            works_per_person=5,
            require_orcid=True,
            require_all_topics=True,
        ),
    )

    assert len(voices) == 1
    assert len(voices[0].works) == 1
    assert voices[0].works[0].id == "https://openalex.org/W2"
