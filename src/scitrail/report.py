"""Markdown report renderer."""

from __future__ import annotations

from scitrail.models import ReportData


def _orcid_value(orcid: str | None) -> str:
    if not orcid:
        return "N/A"
    return orcid


def _work_url(work_id: str) -> str:
    work_id = work_id.strip()
    if work_id.startswith("http://") or work_id.startswith("https://"):
        return work_id
    if work_id.startswith("W"):
        return f"https://openalex.org/{work_id}"
    return work_id


def _doi_url(doi: str) -> str:
    doi = doi.strip()
    if doi.startswith("http://") or doi.startswith("https://"):
        return doi
    if doi.startswith("doi:"):
        doi = doi.split("doi:", maxsplit=1)[1].strip()
    return f"https://doi.org/{doi}"


def render_markdown(report: ReportData) -> str:
    """Render markdown output for the analyzed top-voices report."""

    config = report.config
    lines: list[str] = [
        f"# SciTrail Report: {config.topic}",
        "",
        f"Institution: **{report.institution.display_name}**",
    ]
    if config.department:
        lines.append(f"Department: **{config.department}**")
    lines.extend(
        [
            f"Top voices analyzed: **{len(report.top_voices)}**",
            "",
            "## Executive Summary",
            "",
            report.executive_summary.state_of_art,
            "",
            "### Trends",
        ]
    )
    lines.extend(
        [f"- {trend}" for trend in report.executive_summary.trends] or ["- None"]
    )
    lines.append("")
    lines.append("### Open Questions")
    lines.extend(
        [f"- {question}" for question in report.executive_summary.open_questions]
        or ["- None"]
    )
    lines.append("")

    lines.extend(
        [
            "## Top Voices",
            "",
            "| Name | ORCID | Key Topics |",
            "|---|---|---|",
        ]
    )
    for voice in report.top_voices:
        topics = ", ".join(voice.key_topics[:5]) if voice.key_topics else "N/A"
        lines.append(
            f"| {voice.person_name} | {_orcid_value(voice.orcid)} | {topics} |"
        )

    lines.append("")
    lines.append("## Individual Summaries")
    lines.append("")

    for voice in report.top_voices:
        lines.append(f"### {voice.person_name}")
        lines.append(f"- ORCID: {_orcid_value(voice.orcid)}")
        lines.append(f"- Summary: {voice.state_of_work}")
        lines.append(
            "- Key topics: "
            + (", ".join(voice.key_topics) if voice.key_topics else "N/A")
        )
        lines.append("- Evidence works:")
        if voice.evidence_works:
            lines.extend(
                [
                    (
                        f"  - [{work.title}]("
                        f"{_doi_url(work.doi) if work.doi else _work_url(work.work_id)}"
                        ")"
                    )
                    for work in voice.evidence_works
                ]
            )
        else:
            lines.append("  - None")
        lines.append("")

    return "\n".join(lines)
