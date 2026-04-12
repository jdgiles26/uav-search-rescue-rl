"""Pydantic schemas for API request / response validation."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

class EnvironmentConfig(BaseModel):
    n_service_nodes: int = 20
    n_charging_stations: int = 4
    map_size: int = 100
    time_limit: int = 150
    battery_limit: int = 80
    seed: int = 42


class NodeOut(BaseModel):
    id: int
    x: float
    y: float
    reward: float
    node_type: str
    lat: Optional[float] = None
    lon: Optional[float] = None


class EnvironmentOut(BaseModel):
    nodes: list[NodeOut]
    map_size: int
    time_limit: int
    battery_limit: int
    n_service_nodes: int
    n_charging_stations: int


# ---------------------------------------------------------------------------
# Solver
# ---------------------------------------------------------------------------

class SolveRequest(BaseModel):
    mission_id: int
    algorithm: str = "improved_ql"  # improved_ql | ql_ndts | greedy
    n_uavs: int = 2
    n_episodes: int = 10000


class RouteOut(BaseModel):
    uav_index: int
    node_ids: list[int]
    reward: float
    distance_km: float


class SolveResponse(BaseModel):
    mission_id: int
    algorithm: str
    routes: list[RouteOut]
    total_reward: float
    solve_time_s: float
    cluster_assignments: Optional[list[int]] = None


# ---------------------------------------------------------------------------
# Mission
# ---------------------------------------------------------------------------

class MissionCreate(BaseModel):
    name: str
    theater: str = "Sierra Nevada, CA"
    config: EnvironmentConfig = Field(default_factory=EnvironmentConfig)
    source: str = "manual"


class MissionOut(BaseModel):
    id: int
    name: str
    status: str
    theater: str
    theater_lat: float
    theater_lon: float
    source: str
    algorithm: Optional[str] = None
    total_reward: Optional[float] = None
    solve_time_s: Optional[float] = None
    config: dict
    solution: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    alert_id: Optional[int] = None


class MissionReview(BaseModel):
    action: str  # approve | reject
    reviewed_by: str = "analyst"
    notes: str = ""


# ---------------------------------------------------------------------------
# Alerts / Ingestion
# ---------------------------------------------------------------------------

class AlertOut(BaseModel):
    id: int
    document_name: str
    status: str
    extracted: dict
    confidence: Optional[float] = None
    mission_id: Optional[int] = None
    created_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None


class IngestResponse(BaseModel):
    alert_id: int
    document_name: str
    extracted: dict
    confidence: float
    mission_id: Optional[int] = None
    message: str


# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------

class WSEvent(BaseModel):
    event: str  # alert_created | mission_generated | mission_solved | mission_reviewed
    payload: dict
