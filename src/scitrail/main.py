"""Public entrypoints for scitrail."""

from __future__ import annotations

from pathlib import Path

from scitrail.pipeline import generate_report_file, generate_report_markdown

DEFAULT_EXAMPLE_CONFIG = Path("examples/cu_quantum.yaml")
DEFAULT_EXAMPLE_OUTPUT = Path("examples/cu_quantum_report.md")


def generate_markdown(config_path: str | Path) -> str:
    """Generate a report as markdown text for a YAML config path."""

    return generate_report_markdown(config_path=config_path)


def generate(
    config_path: str | Path,
    output_path: str | Path = "scitrail_report.md",
) -> Path:
    """Generate and persist a markdown report.

    Args:
        config_path: YAML configuration path.
        output_path: Destination markdown path.

    Returns:
        Path to the written report.
    """

    return generate_report_file(config_path=config_path, output_path=output_path)


def generate_example(
    config_path: str | Path = DEFAULT_EXAMPLE_CONFIG,
    output_path: str | Path = DEFAULT_EXAMPLE_OUTPUT,
) -> Path:
    """Run the built-in CU Anschutz + Quantum example end-to-end."""

    return generate(config_path=config_path, output_path=output_path)
