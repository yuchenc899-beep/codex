"""Capability heuristics for pairing fast and deep models to workflows."""

from __future__ import annotations

from research.models import CapabilityProfile, ModelRecommendation


_WORKFLOW_HINTS = {
    "brief": {"reasoning": 2, "tool_calling": 2, "speed": 4, "context": 2},
    "analysis": {"reasoning": 4, "tool_calling": 3, "speed": 3, "context": 4},
    "chat": {"reasoning": 4, "tool_calling": 4, "speed": 4, "context": 4},
    "batch": {"reasoning": 3, "tool_calling": 2, "speed": 5, "context": 3},
    "backtest": {"reasoning": 5, "tool_calling": 2, "speed": 2, "context": 4},
    "paper": {"reasoning": 3, "tool_calling": 3, "speed": 3, "context": 3},
}


def profile_model(name: str) -> CapabilityProfile:
    lowered = name.lower()
    speed = 3
    reasoning = 3
    tool_calling = 3
    context = 3
    cost = 3
    strengths: list[str] = []
    warnings: list[str] = []
    if "mini" in lowered or "flash" in lowered or "turbo" in lowered:
        speed += 2
        cost += 2
        reasoning -= 1
        strengths.append("fast triage")
    if "reason" in lowered or "sonnet" in lowered or "pro" in lowered or "max" in lowered:
        reasoning += 2
        context += 1
        strengths.append("deeper synthesis")
    if "claude" in lowered:
        reasoning += 1
        context += 1
        strengths.append("long-form writing")
    if "gemini" in lowered:
        speed += 1
        tool_calling += 1
        strengths.append("tool-friendly")
    if "gpt" in lowered or "openai" in lowered:
        tool_calling += 1
        strengths.append("balanced generalist")
    if "deepseek" in lowered:
        reasoning += 1
        cost += 1
        warnings.append("verify tool-call reliability for long chains")
    if "qwen" in lowered or "dashscope" in lowered:
        tool_calling += 1
        warnings.append("watch provider-specific formatting quirks")
    speed = max(1, min(5, speed))
    reasoning = max(1, min(5, reasoning))
    tool_calling = max(1, min(5, tool_calling))
    context = max(1, min(5, context))
    cost = max(1, min(5, cost))
    return CapabilityProfile(
        model=name,
        speed=speed,
        reasoning=reasoning,
        tool_calling=tool_calling,
        context_window=context,
        cost_efficiency=cost,
        strengths=strengths,
        warnings=warnings,
    )


def recommend_models(
    workflow: str,
    *,
    quick_candidates: list[str] | None = None,
    deep_candidates: list[str] | None = None,
) -> ModelRecommendation:
    workflow_key = workflow if workflow in _WORKFLOW_HINTS else "analysis"
    requirement = _WORKFLOW_HINTS[workflow_key]
    quick_profiles = [profile_model(item) for item in (quick_candidates or [])]
    deep_profiles = [profile_model(item) for item in (deep_candidates or quick_candidates or [])]
    quick_best = _choose(quick_profiles, requirement, prioritize="speed")
    deep_best = _choose(deep_profiles, requirement, prioritize="reasoning")
    rationale = [
        f"workflow={workflow_key} needs reasoning>={requirement['reasoning']} and tool_calling>={requirement['tool_calling']}",
        "use the fast model for data gathering / low-latency fan-out",
        "use the deep model for synthesis, challenge, and final write-up",
    ]
    warnings: list[str] = []
    if quick_best and quick_best.reasoning < requirement["reasoning"] - 1:
        warnings.append("selected quick model is for triage only; do not use it for final synthesis")
    if deep_best and deep_best.tool_calling < requirement["tool_calling"]:
        warnings.append("selected deep model may need simpler tool plans or pre-fetched context")
    if not quick_profiles:
        warnings.append("no quick candidates provided; recommendation is workflow-level only")
    if not deep_profiles:
        warnings.append("no deep candidates provided; recommendation is workflow-level only")
    profiles = quick_profiles + [item for item in deep_profiles if item.model not in {p.model for p in quick_profiles}]
    return ModelRecommendation(
        workflow=workflow_key,
        quick_model=quick_best.model if quick_best else None,
        deep_model=deep_best.model if deep_best else None,
        rationale=rationale,
        warnings=warnings + (quick_best.warnings if quick_best else []) + (deep_best.warnings if deep_best else []),
        candidate_profiles=profiles,
    )


def render_model_recommendation(result: ModelRecommendation) -> str:
    lines = [
        f"# Model Capability Advice ({result.workflow})",
        "",
        f"- quick_model: {result.quick_model or 'workflow-guidance-only'}",
        f"- deep_model: {result.deep_model or 'workflow-guidance-only'}",
    ]
    lines.append("")
    lines.append("## Rationale")
    for item in result.rationale:
        lines.append(f"- {item}")
    if result.warnings:
        lines.append("")
        lines.append("## Warnings")
        for item in result.warnings:
            lines.append(f"- {item}")
    if result.candidate_profiles:
        lines.append("")
        lines.append("## Candidate Profiles")
        for item in result.candidate_profiles:
            lines.append(
                f"- {item.model}: speed={item.speed} reasoning={item.reasoning} tool_calling={item.tool_calling} context={item.context_window} cost={item.cost_efficiency}"
            )
            for strength in item.strengths:
                lines.append(f"  strength: {strength}")
    return "\n".join(lines)


def _choose(profiles: list[CapabilityProfile], requirement: dict[str, int], *, prioritize: str) -> CapabilityProfile | None:
    if not profiles:
        return None
    best: CapabilityProfile | None = None
    best_score = -10_000
    for profile in profiles:
        score = 0
        score += 3 * min(profile.reasoning, requirement["reasoning"])
        score += 2 * min(profile.tool_calling, requirement["tool_calling"])
        score += 2 * min(profile.context_window, requirement["context"])
        score += 2 * min(profile.speed, requirement["speed"])
        if prioritize == "speed":
            score += profile.speed * 3 + profile.cost_efficiency * 2
        else:
            score += profile.reasoning * 3 + profile.context_window * 2
        if score > best_score:
            best = profile
            best_score = score
    return best
