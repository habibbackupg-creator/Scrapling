from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Any


@dataclass
class MarketingInsight:
    job_id: str
    url: str
    goal: str
    base_score: int
    enhanced_score: int
    business_type: str
    maturity_tier: str
    trend_signal: str
    recommendation: str


def _infer_business_type(url: str, trackers: list[str], cta_links: list[str]) -> str:
    lowered = url.lower()
    if any(token in lowered for token in ("shop", "store", "product", "cart")):
        return "ecommerce"
    if any(token in lowered for token in ("agency", "studio", "consult")):
        return "agency"
    if any("demo" in link.lower() or "pricing" in link.lower() for link in cta_links):
        return "saas"
    if len(trackers) >= 4:
        return "growth"
    return "general"


def _maturity_tier(trackers_count: int, cta_count: int, social_count: int) -> str:
    if trackers_count >= 4 and cta_count >= 2:
        return "sophisticated"
    if trackers_count >= 2 or social_count >= 2:
        return "growth"
    return "bootstrap"


def _trend_signal(previous_scores: list[int], current_score: int) -> tuple[str, int]:
    if not previous_scores:
        return "new", 0

    avg = int(mean(previous_scores))
    delta = current_score - avg
    if delta >= 15:
        return "rising-fast", 12
    if delta >= 7:
        return "rising", 6
    if delta <= -15:
        return "declining-fast", -10
    if delta <= -7:
        return "declining", -5
    return "stable", 0


def build_marketing_insight(
    *,
    job_id: str,
    goal: str,
    extract_payload: dict[str, Any],
    previous_scores: list[int],
) -> MarketingInsight:
    url = str(extract_payload.get("url", ""))
    base_score = int(extract_payload.get("lead_score") or 0)
    trackers = list(extract_payload.get("tracker_hits") or [])
    cta_links = list(extract_payload.get("cta_links") or [])
    social_links = list(extract_payload.get("social_links") or [])

    business_type = _infer_business_type(url, trackers, cta_links)
    maturity = _maturity_tier(len(trackers), len(cta_links), len(social_links))
    trend_signal, trend_bonus = _trend_signal(previous_scores, base_score)

    aggressive_bonus = 0
    if goal in {"lead", "marketing"}:
        aggressive_bonus += 8
    if maturity == "sophisticated":
        aggressive_bonus += 10
    elif maturity == "growth":
        aggressive_bonus += 5

    if business_type == "saas":
        aggressive_bonus += 8
    elif business_type == "ecommerce":
        aggressive_bonus += 6

    enhanced_score = max(0, min(100, base_score + aggressive_bonus + trend_bonus))

    if enhanced_score >= 85:
        recommendation = "hot-enterprise"
    elif enhanced_score >= 70:
        recommendation = "warm-priority"
    elif enhanced_score >= 45:
        recommendation = "nurture"
    else:
        recommendation = "cold"

    return MarketingInsight(
        job_id=job_id,
        url=url,
        goal=goal,
        base_score=base_score,
        enhanced_score=enhanced_score,
        business_type=business_type,
        maturity_tier=maturity,
        trend_signal=trend_signal,
        recommendation=recommendation,
    )
