"""Tests for public main entrypoints."""

from __future__ import annotations

from pathlib import Path

from scitrail.main import generate, generate_example, generate_markdown


def test_generate_markdown_delegates(monkeypatch, sample_config_path: Path) -> None:
    """`generate_markdown` should return the pipeline markdown string."""

    def fake_generate_report_markdown(config_path: str | Path) -> str:
        assert Path(config_path) == sample_config_path
        return "# Test"

    monkeypatch.setattr(
        "scitrail.main.generate_report_markdown",
        fake_generate_report_markdown,
    )

    assert generate_markdown(sample_config_path) == "# Test"


def test_generate_writes_file(
    monkeypatch, sample_config_path: Path, tmp_path: Path
) -> None:
    """`generate` should return the output file path from pipeline."""

    expected = tmp_path / "out.md"

    def fake_generate_report_file(
        config_path: str | Path, output_path: str | Path
    ) -> Path:
        assert Path(config_path) == sample_config_path
        assert Path(output_path) == expected
        return expected

    monkeypatch.setattr("scitrail.main.generate_report_file", fake_generate_report_file)

    assert generate(sample_config_path, expected) == expected


def test_generate_example_uses_defaults(monkeypatch) -> None:
    """`generate_example` should call `generate` with default example paths."""

    expected = Path("examples/cu_quantum_report.md")

    def fake_generate(config_path: str | Path, output_path: str | Path) -> Path:
        assert Path(config_path) == Path("examples/cu_quantum.yaml")
        assert Path(output_path) == expected
        return expected

    monkeypatch.setattr("scitrail.main.generate", fake_generate)

    assert generate_example() == expected
