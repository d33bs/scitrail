"""Candidate disambiguation helpers."""

from __future__ import annotations

from importlib import import_module

from pydantic import BaseModel

from scitrail.models import LLMSettings, VoiceCandidate


class _CanonicalNameResponse(BaseModel):
    """Structured response for canonical name selection."""

    canonical_name: str


def _fallback_canonical_name(candidate: VoiceCandidate) -> str:
    """Pick a deterministic canonical name without an LLM."""

    if candidate.alias_names:
        return sorted(candidate.alias_names, key=len, reverse=True)[0]
    return candidate.display_name


def _llm_canonical_name(
    candidate: VoiceCandidate,
    llm_settings: LLMSettings,
) -> str:
    """Use a local instructor-compatible LLM to pick canonical name."""

    instructor = import_module("instructor")
    llama_cpp_module = import_module("llama_cpp")
    Llama = llama_cpp_module.Llama

    model_path = llm_settings.expanded_cache_dir / llm_settings.model_filename
    llm = Llama(
        model_path=str(model_path),
        n_ctx=llm_settings.model_context_size,
        verbose=False,
    )
    create = instructor.patch(
        create=llm.create_chat_completion_openai_v1,
        mode=instructor.Mode.MD_JSON,
    )
    prompt = (
        "Choose the canonical researcher name from aliases. "
        "Return exactly one best publication name.\n"
        f"Aliases: {', '.join(candidate.alias_names)}"
    )
    response = create(
        response_model=_CanonicalNameResponse,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    return response.canonical_name


def disambiguate_candidates(
    candidates: list[VoiceCandidate],
    *,
    llm_settings: LLMSettings,
    enabled: bool,
) -> list[VoiceCandidate]:
    """Disambiguate candidate names, using LLM where available."""

    if not candidates:
        return candidates

    for candidate in candidates:
        if len(candidate.alias_names) <= 1:
            continue
        if enabled and llm_settings.enabled:
            try:
                candidate.display_name = _llm_canonical_name(candidate, llm_settings)
                continue
            except Exception:
                pass
        candidate.display_name = _fallback_canonical_name(candidate)

    return candidates
