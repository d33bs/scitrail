"""CLI for scitrail."""

from __future__ import annotations

import fire

from scitrail.main import generate, generate_example, generate_markdown


class ScitrailCLI:
    """Command-line interface for report generation."""

    def generate(
        self,
        config: str,
        output: str = "scitrail_report.md",
    ) -> str:
        """Generate a markdown report file from config YAML.

        Args:
            config: Path to YAML configuration.
            output: Output markdown file path.

        Returns:
            Path to generated markdown report.
        """

        output_path = generate(config_path=config, output_path=output)
        return str(output_path)

    def preview(self, config: str) -> str:
        """Print report markdown to stdout without writing a file."""

        markdown = generate_markdown(config_path=config)
        print(markdown)
        return markdown

    def example(
        self,
        config: str = "examples/cu_quantum.yaml",
        output: str = "examples/cu_quantum_report.md",
    ) -> str:
        """Run the built-in example report generation flow."""

        output_path = generate_example(config_path=config, output_path=output)
        return str(output_path)


def trigger() -> None:
    """Run the CLI."""

    fire.Fire(ScitrailCLI)


if __name__ == "__main__":
    trigger()
