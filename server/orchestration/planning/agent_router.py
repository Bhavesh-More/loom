from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, StrictFloat, StrictStr

from orchestration.planning.agent_registry import AGENT_REGISTRY


class RoutingDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent_id: StrictStr = Field(description="The ID of the selected agent")
    capability_score: float = Field(description="The capability match score from 0.0 to 1.0")
    explanation: StrictStr = Field(description="A detailed explanation for why this agent was selected")


def score_agent_capabilities(
    agent_caps: list[str], required_caps: list[str]
) -> tuple[float, list[str], list[tuple[str, str]]]:
    """
    Score the matching capability of an agent against required capabilities.
    Returns:
        tuple[score, list[exact_matches], list[tuple[required, agent_skill]]]
    """
    if not required_caps:
        return 0.0, [], []

    agent_set = {cap.lower().strip() for cap in agent_caps}
    required_clean = [cap.lower().strip() for cap in required_caps]

    exact_matches = []
    partial_matches = []
    matched_required_indices = set()

    # 1. First pass: find exact matches
    for i, req in enumerate(required_clean):
        if req in agent_set:
            exact_matches.append(req)
            matched_required_indices.add(i)

    # 2. Second pass: for unmatched required skills, check for substring matches
    for i, req in enumerate(required_clean):
        if i in matched_required_indices:
            continue
        for agent_cap in agent_set:
            if len(req) >= 3 and len(agent_cap) >= 3:
                if req in agent_cap or agent_cap in req:
                    partial_matches.append((req, agent_cap))
                    matched_required_indices.add(i)
                    break

    # Exact match gets 1.0 weight, partial match gets 0.5 weight
    score = (len(exact_matches) + len(partial_matches) * 0.5) / len(required_caps)
    return min(score, 1.0), exact_matches, partial_matches


def route_task(capabilities_required: list[str] | None) -> RoutingDecision:
    """
    Finds the best-fit agent from the registry based on capability requirements.
    Resolves ties deterministically:
      1. Score (descending)
      2. Specialization: prefer specialized agents over 'all_rounder' when score > 0
      3. Cost category: prefer 'low' over 'medium' over 'high'
      4. Agent ID (ascending/alphabetical)
    """
    req_caps = capabilities_required if capabilities_required is not None else []

    if not req_caps:
        profile = AGENT_REGISTRY["all_rounder"]
        return RoutingDecision(
            agent_id="all_rounder",
            capability_score=1.0,
            explanation=(
                f"No specific capabilities were required for this task. "
                f"Routed to the generalist agent 'all_rounder' (cost: {profile.cost_category})."
            ),
        )

    candidates = []
    for agent_id, profile in AGENT_REGISTRY.items():
        score, exact, partial = score_agent_capabilities(profile.capabilities, req_caps)
        candidates.append({
            "agent_id": agent_id,
            "profile": profile,
            "score": score,
            "exact": exact,
            "partial": partial,
        })

    def cost_rank(cost: str) -> int:
        mapping = {"low": 1, "medium": 2, "high": 3}
        return mapping.get(cost.lower(), 2)

    def sort_key(c):
        score = c["score"]
        is_all_rounder = c["agent_id"] == "all_rounder"
        # Prefer specialized agents (is_all_rounder=False -> 0) over all_rounder (1) if score > 0
        specialization_priority = 1 if (is_all_rounder and score > 0) else 0
        cost = cost_rank(c["profile"].cost_category)
        return (-score, specialization_priority, cost, c["agent_id"])

    candidates.sort(key=sort_key)
    best = candidates[0]
    best_agent_id = best["agent_id"]
    best_score = best["score"]

    matched_skills = best["exact"] + [f"{p[0]}~{p[1]}" for p in best["partial"]]
    matched_str = ", ".join(matched_skills)
    if matched_str:
        best_explanation = (
            f"Selected '{best_agent_id}' (score: {best_score:.2f}) because it matches the required "
            f"capabilities: [{matched_str}]. Agent capabilities: {best['profile'].capabilities}."
        )
    else:
        best_explanation = (
            f"No capability overlap found for required: {req_caps}. "
            f"Routed to fallback/generalist agent '{best_agent_id}' (cost: {best['profile'].cost_category})."
        )

    return RoutingDecision(
        agent_id=best_agent_id,
        capability_score=float(best_score),
        explanation=best_explanation,
    )
