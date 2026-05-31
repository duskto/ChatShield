from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()

engine_kwargs: dict = {"future": True}
if settings.database_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(settings.database_url, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.models import audit_log, rule  # noqa: F401

    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_audit_logs_blocked_stage ON audit_logs (blocked_stage)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_audit_logs_input_blocked ON audit_logs (input_blocked)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_audit_logs_output_blocked ON audit_logs (output_blocked)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_audit_logs_input_risk_level ON audit_logs (input_risk_level)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_audit_logs_output_risk_level ON audit_logs (output_risk_level)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_rules_enabled ON rules (enabled)"))
