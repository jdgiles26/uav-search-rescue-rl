"""Alert queue endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.models.database import get_db, Alert
from backend.models.schemas import AlertOut

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


def _alert_to_out(a: Alert) -> AlertOut:
    return AlertOut(
        id=a.id,
        document_name=a.document_name,
        status=a.status,
        extracted=a.extracted,
        confidence=a.confidence,
        mission_id=a.mission_id,
        created_at=a.created_at,
        processed_at=a.processed_at,
    )


@router.get("", response_model=list[AlertOut])
def list_alerts(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Alert).order_by(Alert.created_at.desc())
    if status:
        q = q.filter(Alert.status == status)
    return [_alert_to_out(a) for a in q.all()]


@router.get("/{alert_id}", response_model=AlertOut)
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    a = db.query(Alert).get(alert_id)
    if not a:
        raise HTTPException(404, "Alert not found")
    return _alert_to_out(a)


@router.post("/{alert_id}/dismiss")
def dismiss_alert(alert_id: int, db: Session = Depends(get_db)):
    a = db.query(Alert).get(alert_id)
    if not a:
        raise HTTPException(404, "Alert not found")
    a.status = "dismissed"
    db.commit()
    return {"dismissed": alert_id}
