import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.schemas.chat import ChatRequest, ModerationContextState
from app.services.api_moderation import moderate_text
from app.services.audit_service import create_audit_log
from app.services.ollama_service import chat_with_ollama
from app.services.rule_group_file_service import learn_keywords_from_ai_detection
from app.services.risk_engine import (
    build_safe_result,
    finalize_detection_result,
    merge_detection_results,
)
from app.services.rule_checker import check_text_by_rules
from app.services.rule_service import list_enabled_rule_snapshots
from app.utils.response import safe_block_reply
from app.utils.time import elapsed_ms, utc_now

router = APIRouter(prefix="/api/chat", tags=["chat"])
MAX_CONTEXT_MESSAGES = 4
MAX_CONTEXT_STATE_MESSAGES = 8
MAX_CONTEXT_CONTENT_CHARS = 160
FOLLOW_UP_ACTION_PATTERNS = (
    r"^(?:那|然后|接着|下一步|之后)[,， ]*(?:怎么|如何)",
    r"^(?:那|然后|接着|下一步|之后)[,， ]*(?:执行|利用|绕过|拿到|导出)",
    r"(?:给我|提供).*(?:命令|脚本|payload|步骤)",
    r"(?:怎么|如何).*(?:执行|利用|绕过|导出|拿到)",
    r"payload",
    r"\bhow (?:do|to)\b",
)


def _compact_context_text(text: str, limit: int = MAX_CONTEXT_CONTENT_CHARS) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1].rstrip() + "…"


def _summarize_context_item(
    role: str,
    content: str,
    custom_rules: list[dict[str, str]],
    detection: dict | None = None,
) -> dict[str, str]:
    compacted = _compact_context_text(content)
    if role != "user":
        return {"role": role, "content": compacted}

    local_detection = detection or check_text_by_rules(content, custom_rules=custom_rules)
    metadata = [
        f"intent={local_detection.get('intent', 'unknown')}",
        f"scenario={local_detection.get('scenario', 'general')}",
        f"actionability={local_detection.get('actionability', 'low')}",
    ]
    if local_detection.get("risk_types"):
        metadata.append(f"risks={','.join(local_detection['risk_types'])}")
    return {
        "role": role,
        "content": f"[{' | '.join(metadata)}] {compacted}",
    }


def _build_context_messages(history: list, custom_rules: list[dict[str, str]]) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    for item in history[-MAX_CONTEXT_MESSAGES:]:
        content = item.content.strip()
        if not content:
            continue
        messages.append(_summarize_context_item(item.role, content, custom_rules))
    return messages


def _load_cached_context_messages(context_state: ModerationContextState | None) -> list[dict[str, str]]:
    if not context_state:
        return []
    return [
        {"role": item.role, "content": item.content.strip()}
        for item in context_state.messages[-MAX_CONTEXT_STATE_MESSAGES:]
        if item.content.strip()
    ]


def _merge_context_messages(*groups: list[dict[str, str]]) -> list[dict[str, str]]:
    merged: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for group in groups:
        for item in group:
            role = str(item.get("role", "")).strip()
            content = str(item.get("content", "")).strip()
            if not role or not content:
                continue
            key = (role, content)
            if key in seen:
                continue
            seen.add(key)
            merged.append({"role": role, "content": content})
    return merged[-MAX_CONTEXT_STATE_MESSAGES:]


def _is_follow_up_action_request(text: str) -> bool:
    normalized = text.strip()
    return any(re.search(pattern, normalized, flags=re.IGNORECASE) for pattern in FOLLOW_UP_ACTION_PATTERNS)


def _apply_context_state_risk_boost(
    text: str,
    rule_result: dict,
    context_state: ModerationContextState | None,
) -> dict:
    if not context_state or not context_state.recent_risk_types:
        return rule_result
    if rule_result.get("actionability") == "high":
        return rule_result
    if not _is_follow_up_action_request(text):
        return rule_result

    boosted_types = sorted(set(rule_result.get("risk_types", [])) | set(context_state.recent_risk_types))
    if not boosted_types:
        return rule_result

    boosted_result = dict(rule_result)
    boosted_result.update(
        {
            "safe": False,
            "risk_level": "high",
            "risk_types": boosted_types,
            "intent": "execute",
            "scenario": "malicious_execution",
            "actionability": "high",
            "reason": (
                f"{rule_result.get('reason', '未发现明显风险')}；"
                "结合最近风险上下文，识别为承接式执行/利用请求"
            ),
        }
    )
    return boosted_result


def _build_next_context_state(
    context_messages: list[dict[str, str]],
    *,
    latest_user_message: dict[str, str],
    latest_user_detection: dict,
    latest_assistant_text: str,
) -> dict:
    next_messages = _merge_context_messages(
        context_messages,
        [latest_user_message, {"role": "assistant", "content": _compact_context_text(latest_assistant_text)}],
    )
    return {
        "messages": next_messages,
        "recent_risk_types": latest_user_detection.get("risk_types", [])[-8:],
    }


def should_force_ai_risk_classification(rule_result: dict) -> bool:
    return not rule_result.get("matched_rules") and not rule_result.get("risk_types")


def maybe_learn_keywords_from_ai(text: str, rule_result: dict, api_result: dict) -> None:
    if not should_force_ai_risk_classification(rule_result):
        return
    if api_result.get("provider") in {None, "none"} or api_result.get("error"):
        return
    if not api_result.get("risk_types"):
        return
    learn_keywords_from_ai_detection(text, api_result.get("risk_types", []))


@router.post("")
async def create_chat(request: ChatRequest, db: Session = Depends(get_db)) -> dict:
    settings = get_settings()
    start_at = utc_now()
    model_name = request.model or settings.ollama_model
    custom_rules = list_enabled_rule_snapshots(db)
    cached_context_messages = _load_cached_context_messages(request.context_state)
    live_context_messages = _build_context_messages(request.history, custom_rules)
    context_messages = _merge_context_messages(cached_context_messages, live_context_messages)

    input_rule_result = _apply_context_state_risk_boost(
        request.message,
        (
            check_text_by_rules(request.message, custom_rules=custom_rules)
            if settings.enable_rule_check
            else build_safe_result(reason="本地规则检测已禁用", provider="rule")
        ),
        request.context_state,
    )
    input_api_result = (
        await moderate_text(
            request.message,
            stage="input",
            require_strict_classification=should_force_ai_risk_classification(input_rule_result),
            context_messages=context_messages,
        )
    )
    maybe_learn_keywords_from_ai(request.message, input_rule_result, input_api_result)
    input_detection = finalize_detection_result(
        merge_detection_results(input_rule_result, input_api_result, stage="input"),
        settings.input_block_threshold,
    )
    current_user_context = _summarize_context_item(
        "user",
        request.message.strip(),
        custom_rules,
        detection=input_detection,
    )
    blocked_context_state = _build_next_context_state(
        context_messages,
        latest_user_message=current_user_context,
        latest_user_detection=input_detection,
        latest_assistant_text=safe_block_reply("input"),
    )

    if input_detection["action"] == "block":
        final_reply = safe_block_reply("input")
        end_at = utc_now()
        create_audit_log(
            db,
            {
                "user_message": request.message if settings.save_raw_text else None,
                "model_name": model_name,
                "model_reply": None,
                "final_reply": final_reply,
                "input_risk_level": input_detection["risk_level"],
                "output_risk_level": None,
                "input_risk_types": input_detection["risk_types"],
                "output_risk_types": [],
                "input_rule_result": input_rule_result,
                "output_rule_result": None,
                "input_api_result": input_api_result,
                "output_api_result": None,
                "input_blocked": True,
                "output_blocked": False,
                "blocked_stage": "input",
                "action": "block",
                "reason": input_detection["reason"],
                "latency_ms": elapsed_ms(start_at, end_at),
            },
        )
        return {
            "success": False,
            "blocked": True,
            "blocked_stage": "input",
            "message": request.message,
            "reply": final_reply,
            "model": model_name,
            "input_detection": input_detection,
            "output_detection": None,
            "context_state": blocked_context_state,
        }

    ollama_result = await chat_with_ollama(request.message, model_name)
    if not ollama_result["success"]:
        end_at = utc_now()
        create_audit_log(
            db,
            {
                "user_message": request.message if settings.save_raw_text else None,
                "model_name": model_name,
                "model_reply": None,
                "final_reply": safe_block_reply("none"),
                "input_risk_level": input_detection["risk_level"],
                "output_risk_level": None,
                "input_risk_types": input_detection["risk_types"],
                "output_risk_types": [],
                "input_rule_result": input_rule_result,
                "output_rule_result": None,
                "input_api_result": input_api_result,
                "output_api_result": None,
                "input_blocked": False,
                "output_blocked": False,
                "blocked_stage": "none",
                "action": "error",
                "reason": ollama_result["error"],
                "latency_ms": elapsed_ms(start_at, end_at),
            },
        )
        raise HTTPException(status_code=502, detail=ollama_result["error"])

    model_reply = ollama_result["reply"]
    output_rule_result = (
        check_text_by_rules(model_reply, custom_rules=custom_rules)
        if settings.enable_rule_check
        else build_safe_result(reason="本地规则检测已禁用", provider="rule")
    )
    output_api_result = (
        await moderate_text(
            model_reply,
            stage="output",
            require_strict_classification=should_force_ai_risk_classification(output_rule_result),
            context_messages=[
                *context_messages,
                current_user_context,
            ],
        )
    )
    maybe_learn_keywords_from_ai(model_reply, output_rule_result, output_api_result)
    output_detection = finalize_detection_result(
        merge_detection_results(output_rule_result, output_api_result, stage="output"),
        settings.output_block_threshold,
    )

    output_blocked = output_detection["action"] == "block"
    final_reply = safe_block_reply("output") if output_blocked else model_reply
    blocked_stage = "output" if output_blocked else "none"
    end_at = utc_now()
    next_context_state = _build_next_context_state(
        context_messages,
        latest_user_message=current_user_context,
        latest_user_detection=input_detection,
        latest_assistant_text=final_reply,
    )

    create_audit_log(
        db,
        {
            "user_message": request.message if settings.save_raw_text else None,
            "model_name": ollama_result["model"],
            "model_reply": model_reply if settings.save_raw_text else None,
            "final_reply": final_reply,
            "input_risk_level": input_detection["risk_level"],
            "output_risk_level": output_detection["risk_level"],
            "input_risk_types": input_detection["risk_types"],
            "output_risk_types": output_detection["risk_types"],
            "input_rule_result": input_rule_result,
            "output_rule_result": output_rule_result,
            "input_api_result": input_api_result,
            "output_api_result": output_api_result,
            "input_blocked": False,
            "output_blocked": output_blocked,
            "blocked_stage": blocked_stage,
            "action": output_detection["action"],
            "reason": output_detection["reason"],
            "latency_ms": elapsed_ms(start_at, end_at),
        },
    )

    return {
        "success": True,
        "blocked": output_blocked,
        "blocked_stage": blocked_stage,
        "message": request.message,
        "reply": final_reply,
        "model": ollama_result["model"],
        "input_detection": input_detection,
        "output_detection": output_detection,
        "context_state": next_context_state,
    }
