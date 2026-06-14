from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.schemas.chat import ChatRequest
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
MAX_CONTEXT_MESSAGES = 6
MAX_CONTEXT_CONTENT_CHARS = 160


def _compact_context_text(text: str, limit: int = MAX_CONTEXT_CONTENT_CHARS) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1].rstrip() + "…"


def _summarize_context_item(role: str, content: str, custom_rules: list[dict[str, str]]) -> dict[str, str]:
    compacted = _compact_context_text(content)
    if role != "user":
        return {"role": role, "content": compacted}

    local_detection = check_text_by_rules(content, custom_rules=custom_rules)
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
    context_messages = _build_context_messages(request.history, custom_rules)

    input_rule_result = (
        check_text_by_rules(request.message, custom_rules=custom_rules)
        if settings.enable_rule_check
        else build_safe_result(reason="本地规则检测已禁用", provider="rule")
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
                _summarize_context_item("user", request.message.strip(), custom_rules),
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
    }
