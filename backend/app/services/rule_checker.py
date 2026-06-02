import re
from functools import lru_cache
from typing import Any

from app.services.rule_group_file_service import get_rule_group_config


RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def _build_default_result() -> dict[str, Any]:
    return {
        "safe": True,
        "risk_level": "low",
        "risk_types": [],
        "matched_rules": [],
        "reason": "未发现明显风险",
    }


def _update_risk_level(current_level: str, new_level: str) -> str:
    return new_level if RISK_ORDER[new_level] > RISK_ORDER[current_level] else current_level


@lru_cache(maxsize=256)
def _compile_custom_pattern(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE)


def _check_custom_rules(text: str, normalized_text: str, custom_rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    matched_rules: list[dict[str, Any]] = []

    for rule in custom_rules:
        pattern = rule.get("pattern", "")
        if not pattern:
            continue

        match_type = rule.get("match_type", "keyword")
        if match_type == "regex":
            try:
                matched = _compile_custom_pattern(pattern).search(text) is not None
            except re.error:
                matched = False
        else:
            matched = pattern.lower() in normalized_text

        if not matched:
            continue

        matched_rules.append(
            {
                "name": rule.get("name", "custom_rule"),
                "keyword": pattern if match_type == "keyword" else None,
                "pattern": pattern if match_type == "regex" else None,
                "risk_level": rule.get("risk_level", "medium"),
                "category": rule.get("category", "unknown"),
                "match_type": match_type,
            }
        )

    return matched_rules


def _append_match(
    matched_rules: list[dict[str, Any]],
    risk_types: set[str],
    risk_level: str,
    *,
    name: str,
    category: str,
    level: str,
    keyword: str | None = None,
    pattern: str | None = None,
    match_type: str,
) -> str:
    matched_rules.append(
        {
            "name": name,
            "keyword": keyword,
            "pattern": pattern,
            "risk_level": level,
            "category": category,
            "match_type": match_type,
        }
    )
    risk_types.add(category)
    return _update_risk_level(risk_level, level)


def _build_reason(risk_type_list: list[str], reason_priority: list[tuple[str, str]]) -> str:
    for category, reason in reason_priority:
        if category in risk_type_list:
            return reason
    return "检测到违规或敏感内容"


def check_text_by_rules(text: str, custom_rules: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    result = _build_default_result()
    if not text or not text.strip():
        return result

    config = get_rule_group_config()
    normalized_text = text.lower()
    matched_rules: list[dict[str, Any]] = []
    risk_types: set[str] = set()
    risk_level = "low"

    for group in config["keyword_groups"]:
        for keyword in group["keywords"]:
            if keyword.lower() not in normalized_text:
                continue
            risk_level = _append_match(
                matched_rules,
                risk_types,
                risk_level,
                name=group["name"],
                category=group["category"],
                level=group["risk_level"],
                keyword=keyword,
                match_type="keyword",
            )

    for rule in config["regex_rules"]:
        if rule["compiled_pattern"].search(text):
            risk_level = _append_match(
                matched_rules,
                risk_types,
                risk_level,
                name=rule["name"],
                category=rule["category"],
                level=rule["risk_level"],
                pattern=rule["pattern"],
                match_type="regex",
            )

    for matched_rule in _check_custom_rules(text, normalized_text, custom_rules or []):
        matched_rules.append(matched_rule)
        risk_types.add(matched_rule["category"])
        risk_level = _update_risk_level(risk_level, matched_rule["risk_level"])

    if not matched_rules:
        return result

    risk_type_list = sorted(risk_types)
    return {
        "safe": False,
        "risk_level": risk_level,
        "risk_types": risk_type_list,
        "matched_rules": matched_rules,
        "reason": _build_reason(risk_type_list, config["reason_priority"]),
    }
