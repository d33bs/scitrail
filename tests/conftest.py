"""Shared fixtures for scitrail tests."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def sample_config_path(tmp_path: Path) -> Path:
    """Write and return a sample YAML configuration file path."""

    path = tmp_path / "config.yaml"
    path.write_text(
        "\n".join(
            [
                "institution: CU Anschutz",
                "department: Department of Biomedical Informatics",
                "topic: Quantum",
                "max_people: 5",
                "works_per_person: 3",
                "lookback_years: 5",
                "llm:",
                "  enabled: false",
            ]
        ),
        encoding="utf-8",
    )
    return path
