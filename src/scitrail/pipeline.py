"""Report generation pipeline."""

from __future__ import annotations

from pathlib import Path

from scitrail.config import load_config
from scitrail.models import ReportData
from scitrail.openalex_client import (
    OpenAlexClient,
    VoiceExtractionOptions,
    extract_top_voices,
)
from scitrail.report import render_markdown
from scitrail.summarizer import build_summarizer


def generate_report_markdown(config_path: str | Path) -> str:
    """Generate a markdown report from a YAML config path."""

    config = load_config(config_path)
    client = OpenAlexClient(settings=config)
    institution = client.resolve_institution(config.institution)
    topic_label = ", ".join(config.active_topics)

    max_records = max(config.max_people * config.works_per_person * 4, 50)
    works_by_id: dict[str, dict[str, object]] = {}
    for topic in config.active_topics:
        topic_works = client.fetch_topic_works(
            topic=topic,
            institution=institution,
            lookback_years=config.lookback_years,
            max_records=max_records,
        )
        for work in topic_works:
            work_id = str(work.get("id", "")).strip()
            if not work_id:
                continue
            existing = works_by_id.get(work_id)
            if existing is None:
                works_by_id[work_id] = work
                continue
            existing_citations = int(existing.get("cited_by_count", 0) or 0)
            candidate_citations = int(work.get("cited_by_count", 0) or 0)
            if candidate_citations > existing_citations:
                works_by_id[work_id] = work
    works = list(works_by_id.values())

    voices = extract_top_voices(
        works=works,
        institution=institution,
        options=VoiceExtractionOptions(
            departments=config.active_departments,
            topics=config.active_topics,
            max_people=config.max_people,
            works_per_person=config.works_per_person,
        ),
    )

    summarizer = build_summarizer(config.llm)
    person_summaries = [
        summarizer.summarize_person(candidate=voice, topic=topic_label)
        for voice in voices
    ]
    executive_summary = summarizer.summarize_executive(
        person_summaries=person_summaries,
        topic=topic_label,
        institution_name=institution.display_name,
    )

    report_data = ReportData(
        config=config,
        institution=institution,
        top_voices=person_summaries,
        executive_summary=executive_summary,
    )

    return render_markdown(report_data)


def generate_report_file(config_path: str | Path, output_path: str | Path) -> Path:
    """Generate markdown report and write it to an output file path."""

    report = generate_report_markdown(config_path=config_path)
    destination = Path(output_path)
    destination.write_text(report, encoding="utf-8")
    return destination
