"""Alert routing: creates alerts from ingested docs, auto-generates missions."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.models.database import Alert, Mission
from backend.services.ingest_service import params_to_env_config
from backend.config import THEATERS


def create_alert(
    db: Session,
    document_name: str,
    document_path: str | None,
    raw_text: str,
    extracted: dict,
    confidence: float,
) -> Alert:
    alert = Alert(
        document_name=document_name,
        document_path=document_path,
        raw_text=raw_text,
        extracted_json=json.dumps(extracted),
        confidence=confidence,
        status="processed",
        processed_at=datetime.now(timezone.utc),
    )
    db.add(alert)
    db.flush()
    return alert


def auto_generate_mission(db: Session, alert: Alert) -> Mission:
    """
    Create a draft mission from an alert's extracted parameters and
    immediately mark it pending_review for an analyst.
    """
    extracted = alert.extracted
    env_config = params_to_env_config(extracted)

    # Resolve theater
    theater = extracted.get("location_name") or "Sierra Nevada, CA"
    if theater in THEATERS:
        lat, lon = THEATERS[theater]
    else:
        lat = extracted.get("latitude") or 36.5785
        lon = extracted.get("longitude") or -118.2923

    n_uavs = env_config.pop("n_uavs", 2)

    mission = Mission(
        name=f"Auto — {alert.document_name}",
        status="pending_review",
        theater=theater,
        theater_lat=lat,
        theater_lon=lon,
        source="auto_ingest",
        config_json=json.dumps({**env_config, "n_uavs": n_uavs}),
        alert_id=alert.id,
    )
    db.add(mission)
    db.flush()

    alert.mission_id = mission.id
    return mission
