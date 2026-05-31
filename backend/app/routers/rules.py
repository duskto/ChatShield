import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.rule import RuleCreate, RuleItem, RuleUpdate
from app.services.rule_service import create_rule, delete_rule, get_rule_by_id, list_rules, update_rule

router = APIRouter(prefix="/api/rules", tags=["rules"])


def validate_rule_payload(match_type: str | None, pattern: str | None) -> None:
    if match_type == "regex" and pattern:
        try:
            re.compile(pattern)
        except re.error as exc:
            raise HTTPException(status_code=422, detail=f"正则表达式无效: {exc}") from exc


@router.get("", response_model=list[RuleItem])
def get_rules(db: Session = Depends(get_db)) -> list[RuleItem]:
    return [RuleItem.model_validate(rule) for rule in list_rules(db)]


@router.post("", response_model=RuleItem, status_code=status.HTTP_201_CREATED)
def post_rule(payload: RuleCreate, db: Session = Depends(get_db)) -> RuleItem:
    validate_rule_payload(payload.match_type, payload.pattern)
    rule = create_rule(db, payload)
    return RuleItem.model_validate(rule)


@router.put("/{rule_id}", response_model=RuleItem)
def put_rule(rule_id: int, payload: RuleUpdate, db: Session = Depends(get_db)) -> RuleItem:
    rule = get_rule_by_id(db, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    validate_rule_payload(payload.match_type or rule.match_type, payload.pattern or rule.pattern)
    updated_rule = update_rule(db, rule, payload)
    return RuleItem.model_validate(updated_rule)


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_rule(rule_id: int, db: Session = Depends(get_db)) -> None:
    rule = get_rule_by_id(db, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    delete_rule(db, rule)
