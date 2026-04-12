"""Solver endpoint — runs RL / greedy algorithms on a mission's environment."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from backend.models.database import get_db, Mission
from backend.models.schemas import SolveRequest, SolveResponse, RouteOut
from backend.services.solver_service import create_environment, solve, serialize_environment
from backend.config import THEATERS
from backend.websocket import manager

router = APIRouter(prefix="/api/solve", tags=["solver"])


async def _solve_and_store(mission_id: int, req: SolveRequest):
    """Run solver in background, persist results, broadcast completion."""
    from backend.models.database import SessionLocal

    db = SessionLocal()
    try:
        mission = db.query(Mission).get(mission_id)
        if not mission:
            return

        config = mission.config
        env = create_environment(config)

        center_lat = mission.theater_lat
        center_lon = mission.theater_lon

        # Store the environment data
        env_data = serialize_environment(env, center_lat, center_lon)
        mission.environment_json = json.dumps(env_data)

        result = solve(
            env,
            algorithm=req.algorithm,
            n_uavs=req.n_uavs,
            n_episodes=req.n_episodes,
            center_lat=center_lat,
            center_lon=center_lon,
        )

        mission.solution_json = json.dumps(result)
        mission.algorithm = result["algorithm"]
        mission.total_reward = result["total_reward"]
        mission.solve_time_s = result["solve_time_s"]

        if mission.status == "pending_review":
            pass  # keep pending_review for auto-ingested missions
        elif mission.status in ("draft", "approved"):
            mission.status = "active"

        db.commit()

        await manager.broadcast("mission_solved", {
            "mission_id": mission_id,
            "total_reward": result["total_reward"],
            "algorithm": result["algorithm"],
        })
    finally:
        db.close()


@router.post("", response_model=SolveResponse)
async def solve_mission(req: SolveRequest, bg: BackgroundTasks, db: Session = Depends(get_db)):
    mission = db.query(Mission).get(req.mission_id)
    if not mission:
        raise HTTPException(404, "Mission not found")

    config = mission.config
    env = create_environment(config)

    result = solve(
        env,
        algorithm=req.algorithm,
        n_uavs=req.n_uavs,
        n_episodes=req.n_episodes,
        center_lat=mission.theater_lat,
        center_lon=mission.theater_lon,
    )

    # Persist
    env_data = serialize_environment(env, mission.theater_lat, mission.theater_lon)
    mission.environment_json = json.dumps(env_data)
    mission.solution_json = json.dumps(result)
    mission.algorithm = result["algorithm"]
    mission.total_reward = result["total_reward"]
    mission.solve_time_s = result["solve_time_s"]

    if mission.status in ("draft", "approved"):
        mission.status = "active"
    db.commit()

    return SolveResponse(
        mission_id=mission.id,
        algorithm=result["algorithm"],
        routes=[RouteOut(**r) for r in result["routes"]],
        total_reward=result["total_reward"],
        solve_time_s=result["solve_time_s"],
        cluster_assignments=result.get("cluster_assignments"),
    )


@router.post("/async")
async def solve_mission_async(req: SolveRequest, bg: BackgroundTasks, db: Session = Depends(get_db)):
    """Kick off solving in the background. Results delivered via WebSocket."""
    mission = db.query(Mission).get(req.mission_id)
    if not mission:
        raise HTTPException(404, "Mission not found")
    bg.add_task(_solve_and_store, mission.id, req)
    return {"status": "solving", "mission_id": mission.id}
