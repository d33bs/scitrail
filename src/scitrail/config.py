"""Configuration loading utilities."""

from __future__ import annotations

from pathlib import Path

import yaml

from scitrail.models import ReportConfig


def load_config(path: str | Path) -> ReportConfig:
    """Load and validate a report config from a YAML file.

    Args:
        path: Path to the YAML configuration file.

    Returns:
        Parsed and validated configuration object.
    """

    config_path = Path(path)
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if payload is None:
        payload = {}
    if not isinstance(payload, dict):
        msg = "Config YAML root must be a mapping/object."
        raise ValueError(msg)
    return ReportConfig.model_validate(payload)
