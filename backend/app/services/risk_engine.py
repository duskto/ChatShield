from typing import Any


RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}
ACTION_MAP = {
    "low": "allow",
    "medium": "allow_with_warning",
    "high": "block",
    "critical": "block",
}
HIGH_PRIORITY_TYPES = {"prompt_injection", "credential_leak", "cyber_abuse"}


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
        "reason": reason,
        "provider": provider,
        "raw": {},
        "sources": [],
        "error": None,
    }


def merge_detection_results(rule_result: dict[str, Any], api_result: dict[str, Any]) -> dict[str, Any]:
    rule_level = normalize_risk_level(rule_result.get("risk_level"))
    api_level = normalize_risk_level(api_result.get("risk_level"))
    risk_types = sorted(set(rule_result.get("risk_types", [])) | set(api_result.get("risk_types", [])))

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

    if HIGH_PRIORITY_TYPES & set(risk_types):
        final_level = compare_risk_levels(final_level, "high")

    reasons = [item for item in [rule_result.get("reason"), api_result.get("reason")] if item]
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


def should_skip_api_moderation(rule_result: dict[str, Any], block_threshold: str) -> bool:
    return is_level_at_least(rule_result.get("risk_level", "low"), block_threshold)
