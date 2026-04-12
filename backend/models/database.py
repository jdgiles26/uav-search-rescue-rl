"""SQLAlchemy models and database setup."""

import json
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    DateTime,
    ForeignKey,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

from backend.config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _utcnow():
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class Mission(Base):
    __tablename__ = "missions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(256), nullable=False)
    status = Column(
        String(32), nullable=False, default="draft",
    )  # draft | pending_review | approved | active | completed | rejected
    theater = Column(String(128), nullable=False, default="Sierra Nevada, CA")
    theater_lat = Column(Float, nullable=False, default=36.5785)
    theater_lon = Column(Float, nullable=False, default=-118.2923)
    source = Column(String(32), nullable=False, default="manual")  # manual | auto_ingest

    # JSON-encoded environment configuration
    config_json = Column(Text, nullable=False, default="{}")
    # JSON-encoded UAVEnvironment serialization (nodes, distances, etc.)
    environment_json = Column(Text, nullable=True)
    # JSON-encoded solution (routes, rewards, algorithm, solve_time)
    solution_json = Column(Text, nullable=True)

    algorithm = Column(String(64), nullable=True)
    total_reward = Column(Float, nullable=True)
    solve_time_s = Column(Float, nullable=True)

    reviewed_by = Column(String(128), nullable=True)
    review_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=True)
    alert = relationship("Alert", back_populates="mission", uselist=False)

    # --- helpers ---
    @property
    def config(self) -> dict:
        return json.loads(self.config_json) if self.config_json else {}

    @config.setter
    def config(self, val: dict):
        self.config_json = json.dumps(val)

    @property
    def solution(self) -> dict | None:
        return json.loads(self.solution_json) if self.solution_json else None

    @solution.setter
    def solution(self, val: dict):
        self.solution_json = json.dumps(val)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    document_name = Column(String(512), nullable=False)
    document_path = Column(String(1024), nullable=True)
    raw_text = Column(Text, nullable=True)

    # JSON-encoded extracted mission parameters
    extracted_json = Column(Text, nullable=False, default="{}")

    status = Column(
        String(32), nullable=False, default="new",
    )  # new | processing | processed | failed | dismissed
    confidence = Column(Float, nullable=True)

    mission_id = Column(Integer, ForeignKey("missions.id"), nullable=True)
    mission = relationship("Mission", back_populates="alert", foreign_keys=[alert_id])

    created_at = Column(DateTime, default=_utcnow)
    processed_at = Column(DateTime, nullable=True)

    # Fix the relationship - use string reference to avoid circular
    mission = relationship(
        "Mission",
        back_populates="alert",
        foreign_keys="[Mission.alert_id]",
    )

    @property
    def extracted(self) -> dict:
        return json.loads(self.extracted_json) if self.extracted_json else {}

    @extracted.setter
    def extracted(self, val: dict):
        self.extracted_json = json.dumps(val)


# Create tables
def init_db():
    Base.metadata.create_all(bind=engine)
