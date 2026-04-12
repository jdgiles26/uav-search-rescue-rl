"""FastAPI application entry-point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.models.database import init_db
from backend.routers import environments, solver, ingest, missions, alerts
from backend.websocket import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="UAV SAR Command Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow the React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(environments.router)
app.include_router(solver.router)
app.include_router(ingest.router)
app.include_router(missions.router)
app.include_router(alerts.router)


# WebSocket
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()  # keep-alive; client can send pings
    except WebSocketDisconnect:
        manager.disconnect(ws)


@app.get("/api/health")
def health():
    return {"status": "ok"}
