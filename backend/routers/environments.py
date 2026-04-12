"""Environment generation and inspection endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.models.database import get_db, Mission
from backend.models.schemas import EnvironmentConfig, EnvironmentOut, NodeOut
from backend.services.solver_service import create_environment, serialize_environment
from backend.config import THEATERS

router = APIRouter(prefix="/api/environments", tags=["environments"])


@router.post("", response_model=EnvironmentOut)
def generate_environment(config: EnvironmentConfig):
    """Generate a standalone environment (not tied to a mission)."""
    env = create_environment(config.model_dump())
    center = THEATERS.get("Sierra Nevada, CA", (36.5785, -118.2923))
    data = serialize_environment(env, center[0], center[1])
    return EnvironmentOut(
        nodes=[NodeOut(**n) for n in data["nodes"]],
        map_size=data["map_size"],
        time_limit=data["time_limit"],
        battery_limit=data["battery_limit"],
        n_service_nodes=data["n_service_nodes"],
        n_charging_stations=data["n_charging_stations"],
    )


@router.get("/theaters")
def list_theaters():
    return {name: {"lat": lat, "lon": lon} for name, (lat, lon) in THEATERS.items()}
