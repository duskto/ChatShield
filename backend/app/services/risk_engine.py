from typing import Any

from app.config import get_settings


RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}
ACTION_MAP = {
    "low": "allow",
    "medium": "allow_with_warning",
    "high": "block",
    "critical": "block",
}
HIGH_PRIORITY_TYPES = {
    "prompt_injection",
    "jailbreak",
    "prompt_leakage",
    "policy_evasion",
    "data_exfiltration",
    "credential_leak",
    "tool_abuse",
    "cyber_abuse",
    "malware",
    "illegal",
    "fraud",
    "impersonation",
    "extremism",
}
SAFE_INTENTS = {"discuss", "analyze", "translate", "audit"}
DANGEROUS_INTENTS = {"generate", "execute", "bypass"}
ACTIONABILITY_ORDER = {"low": 0, "medium": 1, "high": 2}
SAFE_OUTPUT_SCENARIOS = {
    "security_explanation",
    "security_analysis",
    "content_transformation",
    "log_analysis",
    "code_review",
}


def normalize_risk_level(level: str | None) -> str:
    if not level:
        return "low"
    level = level.lower().strip()
    return level if level in RISK_ORDER else "low"


def compare_risk_levels(left: str, right: str) -> str:
    left = normalize_risk_level(left)
    right = normalize_risk_level(right)
    return left if RISK_ORDER[left] >= RISK_ORDER[right] else right


def is_level_at_least(level: str, threshold: str) -> bool:
    return RISK_ORDER[normalize_risk_level(level)] >= RISK_ORDER[normalize_risk_level(threshold)]


def build_safe_result(reason: str = "未发现明显风险", provider: str | None = None) -> dict[str, Any]:
    return {
        "safe": True,
        "risk_level": "low",
        "risk_types": [],
        "matched_rules": [],
        "action": "allow",
        "intent": "unknown",
        "scenario": "general",
        "actionability": "low",
        "reason": reason,
        "provider": provider,
        "raw": {},
        "sources": [],
        "error": None,
    }


def _rule_categories(rule_result: dict[str, Any]) -> set[str]:
    return set(rule_result.get("risk_types", []))


def _matched_rules_are_keyword_only(rule_result: dict[str, Any]) -> bool:
    matched_rules = rule_result.get("matched_rules", [])
    return bool(matched_rules) and all(item.get("match_type") == "keyword" for item in matched_rules)


def _matched_rules_are_local_pattern_only(rule_result: dict[str, Any]) -> bool:
    matched_rules = rule_result.get("matched_rules", [])
    return bool(matched_rules) and all(item.get("match_type") in {"keyword", "regex"} for item in matched_rules)


def _normalize_intent(intent: str | None) -> str:
    normalized = (intent or "unknown").strip().lower()
    return normalized if normalized in SAFE_INTENTS | DANGEROUS_INTENTS | {"unknown"} else "unknown"


def _normalize_actionability(actionability: str | None) -> str:
    normalized = (actionability or "low").strip().lower()
    return normalized if normalized in ACTIONABILITY_ORDER else "low"


def _resolve_intent(rule_result: dict[str, Any], api_result: dict[str, Any]) -> str:
    api_intent = _normalize_intent(api_result.get("intent"))
    rule_intent = _normalize_intent(rule_result.get("intent"))
    return api_intent if api_intent != "unknown" else rule_intent


def _resolve_scenario(rule_result: dict[str, Any], api_result: dict[str, Any]) -> str:
    api_scenario = str(api_result.get("scenario", "general")).strip().lower()
    if api_scenario and api_scenario != "general":
        return api_scenario
    return str(rule_result.get("scenario", "general")).strip().lower() or "general"


def _resolve_actionability(rule_result: dict[str, Any], api_result: dict[str, Any]) -> str:
    rule_actionability = _normalize_actionability(rule_result.get("actionability"))
    api_actionability = _normalize_actionability(api_result.get("actionability"))
    return rule_actionability if ACTIONABILITY_ORDER[rule_actionability] >= ACTIONABILITY_ORDER[api_actionability] else api_actionability


def _should_apply_api_override(rule_result: dict[str, Any], api_result: dict[str, Any], *, stage: str) -> bool:
    if api_result.get("provider") in {None, "none"} or api_result.get("error"):
        return False

    reviewable_rule_types = get_settings().api_reviewable_rule_type_set
    rule_level = normalize_risk_level(rule_result.get("risk_level"))
    api_level = normalize_risk_level(api_result.get("risk_level"))
    rule_categories = _rule_categories(rule_result)
    api_intent = _normalize_intent(api_result.get("intent"))
    api_actionability = _normalize_actionability(api_result.get("actionability"))
    api_scenario = _resolve_scenario({}, api_result)

    if rule_level not in {"medium", "high", "critical"} or api_level != "low":
        return False
    if api_intent not in SAFE_INTENTS or api_actionability != "low":
        return False
    if stage == "output":
        return _matched_rules_are_local_pattern_only(rule_result) and api_scenario in SAFE_OUTPUT_SCENARIOS
    if not _matched_rules_are_keyword_only(rule_result):
        return False
    if not rule_categories or not rule_categories.issubset(reviewable_rule_types):
        return False
    return True


def merge_detection_results(rule_result: dict[str, Any], api_result: dict[str, Any], *, stage: str = "input") -> dict[str, Any]:
    rule_level = normalize_risk_level(rule_result.get("risk_level"))
    api_level = normalize_risk_level(api_result.get("risk_level"))
    risk_types = sorted(set(rule_result.get("risk_types", [])) | set(api_result.get("risk_types", [])))
    apply_api_override = _should_apply_api_override(rule_result, api_result, stage=stage)
    final_intent = _resolve_intent(rule_result, api_result)
    final_scenario = _resolve_scenario(rule_result, api_result)
    final_actionability = _resolve_actionability(rule_result, api_result)

    if rule_level == "critical" or api_level == "critical":
        final_level = "critical"
    elif rule_level == "high" or api_level == "high":
        final_level = "high"
    elif rule_level == "medium" and api_level == "medium":
        final_level = "medium" if set(risk_types) == {"privacy"} else "high"
    elif rule_level == "medium" or api_level == "medium":
        final_level = "medium"
    else:
        final_level = "low"

    if apply_api_override:
        final_level = "medium"

    if final_intent in DANGEROUS_INTENTS and final_actionability == "high" and risk_types:
        final_level = compare_risk_levels(final_level, "high")

    if HIGH_PRIORITY_TYPES & set(risk_types):
        final_level = compare_risk_levels(final_level, "high")
        if apply_api_override:
            final_level = "medium"

    reasons = [item for item in [rule_result.get("reason"), api_result.get("reason")] if item]
    if apply_api_override:
        reasons.append("API 语义审核判定为解释/讨论类低风险，已下调本地关键词命中结果")
    sources = []
    if rule_result:
        sources.append("rule")
    if api_result.get("provider") not in {None, "none"} or api_result.get("error"):
        sources.append("api")

    result = build_safe_result(reason="；".join(dict.fromkeys(reasons)) or "未发现明显风险")
    result.update(
        {
            "safe": final_level == "low",
            "risk_level": final_level,
            "risk_types": risk_types,
            "matched_rules": rule_result.get("matched_rules", []),
            "action": ACTION_MAP[final_level],
            "intent": final_intent,
            "scenario": final_scenario,
            "actionability": final_actionability,
            "provider": api_result.get("provider"),
            "raw": {
                "rule": rule_result.get("raw", {}),
                "api": api_result.get("raw", {}),
            },
            "sources": sources,
            "error": api_result.get("error"),
        }
    )
    return result


def finalize_detection_result(result: dict[str, Any], block_threshold: str) -> dict[str, Any]:
    threshold = normalize_risk_level(block_threshold)
    result = {**result}
    result["safe"] = not is_level_at_least(result.get("risk_level", "low"), threshold)
    result["action"] = (
        "block"
        if is_level_at_least(result.get("risk_level", "low"), threshold)
        else ACTION_MAP[normalize_risk_level(result.get("risk_level", "low"))]
    )
    return result
