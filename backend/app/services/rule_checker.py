import re
from functools import lru_cache
from typing import Any

from app.services.rule_group_file_service import get_rule_group_config


RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}
CONTEXTUAL_DOWNGRADE_CATEGORIES = {
    "prompt_injection",
    "jailbreak",
    "prompt_leakage",
    "policy_evasion",
    "data_exfiltration",
    "tool_abuse",
    "cyber_abuse",
    "malware",
    "illegal",
    "fraud",
    "impersonation",
    "extremism",
}
EXPLANATORY_OR_DEFENSIVE_PATTERNS = (
    r"什么意思",
    r"是什么",
    r"解释(?:一下)?",
    r"含义",
    r"介绍(?:一下)?",
    r"科普",
    r"了解(?:一下)?",
    r"原理",
    r"作用",
    r"风险",
    r"危害",
    r"为什么",
    r"如何防范",
    r"怎么防范",
    r"如何检测",
    r"怎么检测",
    r"区别",
    r"意思是",
    r"是指",
    r"表示",
    r"通常指",
    r"这个命令会",
    r"该命令会",
    r"不要执行",
    r"请勿执行",
    r"仅用于学习",
    r"仅作演示",
    r"仅用于测试",
    r"\bwhat does\b",
    r"\bwhat is\b",
    r"\bmeaning of\b",
    r"\bexplain\b",
    r"\brefers to\b",
    r"\bmeans\b",
    r"\bwhy is\b",
    r"\bdanger(?:ous)?\b",
    r"\bdo not run\b",
    r"\bfor learning\b",
    r"\bfor education(?:al)?\b",
    r"\bfor testing only\b",
    r"\bthis command will\b",
)
ACTIONABLE_REQUEST_PATTERNS = (
    r"帮我执行",
    r"请执行",
    r"执行以下命令",
    r"在shell中执行",
    r"请运行",
    r"帮我运行",
    r"运行以下命令",
    r"给我命令",
    r"给我脚本",
    r"命令如下",
    r"脚本如下",
    r"代码如下",
    r"你可以运行",
    r"可以执行",
    r"运行这个命令",
    r"执行这个命令",
    r"如何执行",
    r"怎么执行",
    r"如何实现",
    r"怎么做",
    r"提供步骤",
    r"写一个.*脚本",
    r"生成.*payload",
    r"绕过",
    r"提权",
    r"爆破",
    r"\bexecute the following\b",
    r"\brun the following\b",
    r"\brun this command\b",
    r"\bexecute this command\b",
    r"\bgive me (?:the )?command\b",
    r"\bgive me (?:a )?script\b",
    r"\bwrite (?:me )?(?:a )?script\b",
    r"\bprovide (?:the )?steps\b",
    r"\bhow to execute\b",
    r"\bhow to do\b",
    r"\bhow to implement\b",
    r"\bbypass\b",
    r"\bexploit\b",
    r"\bprivilege escalation\b",
)
ANALYTICAL_PATTERNS = (
    r"分析",
    r"审计",
    r"日志",
    r"复盘",
    r"排查",
    r"review",
    r"audit",
    r"analy(?:s|z)e",
    r"log",
    r"trace",
)
TRANSLATION_PATTERNS = (
    r"翻译",
    r"转述",
    r"总结",
    r"概括",
    r"translate",
    r"summarize",
    r"paraphrase",
)


def _build_default_result() -> dict[str, Any]:
    return {
        "safe": True,
        "risk_level": "low",
        "risk_types": [],
        "matched_rules": [],
        "intent": "unknown",
        "scenario": "general",
        "actionability": "low",
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


def _text_matches_any_pattern(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def _is_explanatory_or_defensive_context(text: str) -> bool:
    return _text_matches_any_pattern(text, EXPLANATORY_OR_DEFENSIVE_PATTERNS) and not _text_matches_any_pattern(
        text,
        ACTIONABLE_REQUEST_PATTERNS,
    )


def _apply_contextual_risk_adjustment(
    text: str,
    *,
    risk_level: str,
    risk_types: list[str],
    reason: str,
) -> tuple[str, str]:
    if risk_level not in {"high", "critical"}:
        return risk_level, reason
    if not risk_types or not set(risk_types).issubset(CONTEXTUAL_DOWNGRADE_CATEGORIES):
        return risk_level, reason
    if not _is_explanatory_or_defensive_context(text):
        return risk_level, reason
    return "medium", f"{reason}；检测到解释/科普/防御性语境，已降级为观察放行"


def _infer_local_scene(text: str, risk_types: list[str]) -> dict[str, str]:
    normalized_text = text.strip()
    if _text_matches_any_pattern(normalized_text, ACTIONABLE_REQUEST_PATTERNS):
        if re.search(r"(请执行|帮我执行|请运行|帮我运行|execute|run)", normalized_text, flags=re.IGNORECASE):
            scenario = "malicious_execution"
            intent = "execute"
        elif re.search(
            r"(给我|提供|写一个|生成).*(脚本|payload|命令|步骤|script|payload|command|steps)",
            normalized_text,
            flags=re.IGNORECASE,
        ):
            scenario = "malicious_generation"
            intent = "generate"
        elif re.search(r"(绕过|bypass|提权|execute|run|执行|运行)", normalized_text, flags=re.IGNORECASE):
            scenario = "malicious_execution"
            intent = "execute"
        else:
            scenario = "malicious_request"
            intent = "bypass"
        return {
            "intent": intent,
            "scenario": scenario,
            "actionability": "high",
        }

    if _text_matches_any_pattern(normalized_text, TRANSLATION_PATTERNS):
        return {
            "intent": "translate",
            "scenario": "content_transformation",
            "actionability": "low",
        }

    if _text_matches_any_pattern(normalized_text, ANALYTICAL_PATTERNS):
        return {
            "intent": "analyze",
            "scenario": "security_analysis",
            "actionability": "low",
        }

    if _is_explanatory_or_defensive_context(normalized_text):
        return {
            "intent": "discuss",
            "scenario": "security_explanation",
            "actionability": "low",
        }

    if risk_types:
        return {
            "intent": "unknown",
            "scenario": "risk_mention",
            "actionability": "medium",
        }

    return {
        "intent": "unknown",
        "scenario": "general",
        "actionability": "low",
    }


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
    risk_level, reason = _apply_contextual_risk_adjustment(
        text,
        risk_level=risk_level,
        risk_types=risk_type_list,
        reason=_build_reason(risk_type_list, config["reason_priority"]),
    )
    local_scene = _infer_local_scene(text, risk_type_list)
    return {
        "safe": False,
        "risk_level": risk_level,
        "risk_types": risk_type_list,
        "matched_rules": matched_rules,
        "intent": local_scene["intent"],
        "scenario": local_scene["scenario"],
        "actionability": local_scene["actionability"],
        "reason": reason,
    }
