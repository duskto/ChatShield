from threading import Lock

from sqlalchemy.orm import Session

from app.models.rule import Rule
from app.schemas.rule import RuleCreate, RuleUpdate


_enabled_rule_snapshots_cache: list[dict[str, str]] | None = None
_enabled_rule_snapshots_lock = Lock()


def _invalidate_enabled_rule_snapshots_cache() -> None:
    global _enabled_rule_snapshots_cache
    with _enabled_rule_snapshots_lock:
        _enabled_rule_snapshots_cache = None


def list_rules(db: Session) -> list[Rule]:
    return db.query(Rule).order_by(Rule.created_at.desc(), Rule.id.desc()).all()


def list_enabled_rules(db: Session) -> list[Rule]:
    return (
        db.query(Rule)
        .filter(Rule.enabled.is_(True))
        .order_by(Rule.created_at.desc(), Rule.id.desc())
        .all()
    )


def list_enabled_rule_snapshots(db: Session) -> list[dict[str, str]]:
    global _enabled_rule_snapshots_cache

    cached = _enabled_rule_snapshots_cache
    if cached is not None:
        return cached

    with _enabled_rule_snapshots_lock:
        cached = _enabled_rule_snapshots_cache
        if cached is not None:
            return cached

        snapshots = [
            {
                "name": name,
                "category": category,
                "pattern": pattern,
                "match_type": match_type,
                "risk_level": risk_level,
            }
            for name, category, pattern, match_type, risk_level in (
                db.query(
                    Rule.name,
                    Rule.category,
                    Rule.pattern,
                    Rule.match_type,
                    Rule.risk_level,
                )
                .filter(Rule.enabled.is_(True))
                .order_by(Rule.created_at.desc(), Rule.id.desc())
                .all()
            )
        ]
        _enabled_rule_snapshots_cache = snapshots
        return snapshots


def get_rule_by_id(db: Session, rule_id: int) -> Rule | None:
    return db.query(Rule).filter(Rule.id == rule_id).first()


def create_rule(db: Session, payload: RuleCreate) -> Rule:
    rule = Rule(**payload.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    _invalidate_enabled_rule_snapshots_cache()
    return rule


def update_rule(db: Session, rule: Rule, payload: RuleUpdate) -> Rule:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, key, value)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    _invalidate_enabled_rule_snapshots_cache()
    return rule


def delete_rule(db: Session, rule: Rule) -> None:
    db.delete(rule)
    db.commit()
    _invalidate_enabled_rule_snapshots_cache()
