from sqlalchemy.orm import Session

from app.models.rule import Rule
from app.schemas.rule import RuleCreate, RuleUpdate


def list_rules(db: Session) -> list[Rule]:
    return db.query(Rule).order_by(Rule.created_at.desc(), Rule.id.desc()).all()


def list_enabled_rules(db: Session) -> list[Rule]:
    return (
        db.query(Rule)
        .filter(Rule.enabled.is_(True))
        .order_by(Rule.created_at.desc(), Rule.id.desc())
        .all()
    )


def get_rule_by_id(db: Session, rule_id: int) -> Rule | None:
    return db.query(Rule).filter(Rule.id == rule_id).first()


def create_rule(db: Session, payload: RuleCreate) -> Rule:
    rule = Rule(**payload.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def update_rule(db: Session, rule: Rule, payload: RuleUpdate) -> Rule:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, key, value)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def delete_rule(db: Session, rule: Rule) -> None:
    db.delete(rule)
    db.commit()

