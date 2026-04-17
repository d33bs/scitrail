"""Tests for configuration parsing."""

from __future__ import annotations

from pathlib import Path

from scitrail.config import load_config


def test_load_config(sample_config_path: Path) -> None:
    """Config loader should parse expected defaults and values."""

    config = load_config(sample_config_path)
    assert config.institution == "CU Anschutz"
    assert config.department == "Department of Biomedical Informatics"
    assert config.topic == "Quantum"
    assert config.max_people == 5
    assert config.works_per_person == 3
    assert config.llm.enabled is False


def test_load_config_invalid_root(tmp_path: Path) -> None:
    """Config loader should reject non-mapping YAML roots."""

    bad = tmp_path / "bad.yaml"
    bad.write_text("- one\n- two\n", encoding="utf-8")

    try:
        load_config(bad)
    except ValueError as error:
        assert "root must be a mapping" in str(error)
    else:
        raise AssertionError("Expected ValueError for invalid YAML root")
