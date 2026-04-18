# scitrail

`scitrail` builds an easy-to-read markdown report of the top voices in a field,
including ORCID identifiers and a concise state-of-the-art executive summary.

The workflow is:

1. Read a YAML config (`institution`, optional `department`/`departments`, `topic`/`topics`, and simple knobs).
1. Resolve the institution in OpenAlex (with ROR when available).
1. Scan topic-relevant literature in that institution.
1. Rank the top voices (configurable count).
1. Summarize each voice and produce an executive summary.
1. Render a markdown report.

## Install

```bash
uv sync
```

Optional local model support (for local LLM summarization with `instructor`):

```bash
uv sync --extra local-llm
```

## Example config

```yaml
institution: CU Anschutz
departments:
  - Department of Biomedical Informatics
topics:
  - Quantum
  - Artificial intelligence
max_people: 5
works_per_person: 8
lookback_years: 5
openalex_email: you@example.org
# openalex_api_key: <optional>
llm:
  enabled: false
```

## CLI

Generate a markdown report file:

```bash
uv run scitrail generate --config examples/cu_quantum.yaml --output report.md
```

Preview markdown in terminal:

```bash
uv run scitrail preview --config examples/cu_quantum.yaml
```

Compare department-scoped vs all-departments runs:

```bash
uv run scitrail generate --config examples/cu_topics_dbmi.yaml --output examples/cu_topics_dbmi_report.md
uv run scitrail generate --config examples/cu_topics_all_departments.yaml --output examples/cu_topics_all_departments_report.md
```

Run the built-in example end-to-end and write `examples/cu_quantum_report.md`:

```bash
uv run scitrail example
```

Execute the docs notebook version (renders rich markdown output in the notebook):

```bash
uv run --group docs --group notebooks poe docs-notebook-cu-quantum
```

## Notes

- OpenAlex API keys are recommended for non-trivial usage.
- If local LLM dependencies are unavailable, scitrail automatically falls back to
  deterministic summaries so reports still complete.
