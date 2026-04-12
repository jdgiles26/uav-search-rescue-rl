"""Document ingestion endpoint — upload PDF/text, auto-extract mission params."""

from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session

from backend.config import UPLOAD_DIR
from backend.models.database import get_db
from backend.models.schemas import IngestResponse
from backend.services.ingest_service import extract_text_from_file, extract_mission_params
from backend.services.alert_service import create_alert, auto_generate_mission
from backend.websocket import manager

router = APIRouter(prefix="/api/ingest", tags=["ingestion"])


@router.post("", response_model=IngestResponse)
async def ingest_document(
    file: UploadFile = File(...),
    auto_solve: bool = True,
    db: Session = Depends(get_db),
    bg: BackgroundTasks = BackgroundTasks(),
):
    """
    Upload a SAR document (PDF or text).

    Pipeline:
    1. Save file
    2. Extract raw text
    3. AI-extract mission parameters
    4. Create alert record
    5. Auto-generate a pending_review mission
    6. (optional) Kick off solver in background
    """
    # 1 — Save
    dest = UPLOAD_DIR / file.filename
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # 2 — Extract text
    try:
        raw_text = extract_text_from_file(str(dest))
    except Exception as exc:
        raise HTTPException(422, f"Could not extract text: {exc}")

    if not raw_text.strip():
        raise HTTPException(422, "Document produced no extractable text")

    # 3 — AI extraction
    extracted, confidence = extract_mission_params(raw_text)

    # 4 — Alert
    alert = create_alert(
        db,
        document_name=file.filename,
        document_path=str(dest),
        raw_text=raw_text,
        extracted=extracted,
        confidence=confidence,
    )

    # 5 — Auto-generate mission
    mission = auto_generate_mission(db, alert)
    db.commit()

    # Broadcast
    await manager.broadcast("alert_created", {
        "alert_id": alert.id,
        "document_name": file.filename,
        "confidence": confidence,
        "mission_id": mission.id,
    })

    # 6 — Optional auto-solve
    if auto_solve and confidence >= 0.3:
        from backend.routers.solver import _solve_and_store
        from backend.models.schemas import SolveRequest

        config = mission.config
        n_uavs = config.get("n_uavs", 2)
        req = SolveRequest(
            mission_id=mission.id,
            algorithm="improved_ql",
            n_uavs=n_uavs,
            n_episodes=10000,
        )
        bg.add_task(_solve_and_store, mission.id, req)

    return IngestResponse(
        alert_id=alert.id,
        document_name=file.filename,
        extracted=extracted,
        confidence=confidence,
        mission_id=mission.id,
        message=(
            "Mission auto-generated and solver started"
            if auto_solve and confidence >= 0.3
            else "Mission auto-generated — awaiting manual solve"
        ),
    )
