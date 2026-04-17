"""Tests for scitrail CLI module."""

from __future__ import annotations

from pathlib import Path

from scitrail.cli import ScitrailCLI


def test_cli_generate(monkeypatch, sample_config_path: Path, tmp_path: Path) -> None:
    """CLI generate should return the output path string."""

    output = tmp_path / "report.md"

    def fake_generate(config_path: str | Path, output_path: str | Path) -> Path:
        assert Path(config_path) == sample_config_path
        assert Path(output_path) == output
        return output

    monkeypatch.setattr("scitrail.cli.generate", fake_generate)

    cli = ScitrailCLI()
    result = cli.generate(config=str(sample_config_path), output=str(output))
    assert result == str(output)


def test_cli_preview(monkeypatch, capsys, sample_config_path: Path) -> None:
    """CLI preview should print markdown and return it."""

    def fake_generate_markdown(config_path: str | Path) -> str:
        assert Path(config_path) == sample_config_path
        return "# Preview"

    monkeypatch.setattr("scitrail.cli.generate_markdown", fake_generate_markdown)

    cli = ScitrailCLI()
    result = cli.preview(config=str(sample_config_path))
    captured = capsys.readouterr()
    assert result == "# Preview"
    assert "# Preview" in captured.out


def test_cli_example(monkeypatch, tmp_path: Path) -> None:
    """CLI example should return generated example output path."""

    output = tmp_path / "example_report.md"

    def fake_generate_example(config_path: str | Path, output_path: str | Path) -> Path:
        assert Path(config_path) == Path("examples/cu_quantum.yaml")
        assert Path(output_path) == output
        return output

    monkeypatch.setattr("scitrail.cli.generate_example", fake_generate_example)

    cli = ScitrailCLI()
    result = cli.example(output=str(output))
    assert result == str(output)
