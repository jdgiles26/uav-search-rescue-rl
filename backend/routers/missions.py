"""Mission CRUD + review workflow."""

from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.models.database import get_db, Mission
from backend.models.schemas import MissionCreate, MissionOut, MissionReview
from backend.config import THEATERS
from backend.websocket import manager

router = APIRouter(prefix="/api/missions", tags=["missions"])


def _mission_to_out(m: Mission) -> MissionOut:
    return MissionOut(
        id=m.id,
        name=m.name,
        status=m.status,
        theater=m.theater,
        theater_lat=m.theater_lat,
        theater_lon=m.theater_lon,
        source=m.source,
        algorithm=m.algorithm,
        total_reward=m.total_reward,
        solve_time_s=m.solve_time_s,
        config=m.config,
        solution=m.solution,
        created_at=m.created_at,
        updated_at=m.updated_at,
        alert_id=m.alert_id,
    )


@router.get("", response_model=list[MissionOut])
def list_missions(
    status: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Mission).order_by(Mission.created_at.desc())
    if status:
        q = q.filter(Mission.status == status)
    if source:
        q = q.filter(Mission.source == source)
    return [_mission_to_out(m) for m in q.all()]


@router.post("", response_model=MissionOut)
def create_mission(body: MissionCreate, db: Session = Depends(get_db)):
    theater = body.theater
    lat, lon = THEATERS.get(theater, (36.5785, -118.2923))

    m = Mission(
        name=body.name,
        status="draft",
        theater=theater,
        theater_lat=lat,
        theater_lon=lon,
        source=body.source,
        config_json=body.config.model_dump_json(),
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return _mission_to_out(m)


@router.get("/{mission_id}", response_model=MissionOut)
def get_mission(mission_id: int, db: Session = Depends(get_db)):
    m = db.query(Mission).get(mission_id)
    if not m:
        raise HTTPException(404, "Mission not found")
    return _mission_to_out(m)


@router.delete("/{mission_id}")
def delete_mission(mission_id: int, db: Session = Depends(get_db)):
    m = db.query(Mission).get(mission_id)
    if not m:
        raise HTTPException(404, "Mission not found")
    db.delete(m)
    db.commit()
    return {"deleted": mission_id}


@router.post("/{mission_id}/review", response_model=MissionOut)
async def review_mission(
    mission_id: int,
    body: MissionReview,
    db: Session = Depends(get_db),
):
    """Analyst approves or rejects a pending_review mission."""
    m = db.query(Mission).get(mission_id)
    if not m:
        raise HTTPException(404, "Mission not found")
    if m.status != "pending_review":
        raise HTTPException(400, f"Mission is '{m.status}', not pending_review")

    if body.action == "approve":
        m.status = "approved"
    elif body.action == "reject":
        m.status = "rejected"
    else:
        raise HTTPException(400, "action must be 'approve' or 'reject'")

    m.reviewed_by = body.reviewed_by
    m.review_notes = body.notes
    db.commit()
    db.refresh(m)

    await manager.broadcast("mission_reviewed", {
        "mission_id": m.id,
        "status": m.status,
        "reviewed_by": m.reviewed_by,
    })

    return _mission_to_out(m)
