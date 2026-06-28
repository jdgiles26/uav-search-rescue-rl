/**
 * Thin API client for the FastAPI backend.
 * Vite proxies /api and /ws to localhost:8000.
 */

import type { Mission, Alert, EnvironmentConfig, Solution } from "../types";

const API_BASE = (import.meta.env.VITE_API_BASE_URL || window.location.origin).replace(
  /\/+$/,
  ""
);
const WS_URL = import.meta.env.VITE_WS_URL;

function apiUrl(path: string): string {
  return `${API_BASE}${path}`;
}

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status}: ${body}`);
  }
  return res.json();
}

// ---- Missions ----

export async function listMissions(
  status?: string,
  source?: string
): Promise<Mission[]> {
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  if (source) params.set("source", source);
  return json(await fetch(apiUrl(`/api/missions?${params}`)));
}

export async function getMission(id: number): Promise<Mission> {
  return json(await fetch(apiUrl(`/api/missions/${id}`)));
}

export async function createMission(body: {
  name: string;
  theater: string;
  config: EnvironmentConfig;
  source?: string;
}): Promise<Mission> {
  return json(
    await fetch(apiUrl("/api/missions"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
  );
}

export async function deleteMission(id: number): Promise<void> {
  await fetch(apiUrl(`/api/missions/${id}`), { method: "DELETE" });
}

export async function reviewMission(
  id: number,
  action: "approve" | "reject",
  reviewedBy = "analyst",
  notes = ""
): Promise<Mission> {
  return json(
    await fetch(apiUrl(`/api/missions/${id}/review`), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, reviewed_by: reviewedBy, notes }),
    })
  );
}

// ---- Solver ----

export async function solveMission(body: {
  mission_id: number;
  algorithm: string;
  n_uavs: number;
  n_episodes: number;
}): Promise<Solution & { mission_id: number }> {
  return json(
    await fetch(apiUrl("/api/solve"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
  );
}

// ---- Environments ----

export async function generateEnvironment(config: EnvironmentConfig) {
  return json(
    await fetch(apiUrl("/api/environments"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    })
  );
}

export async function listTheaters(): Promise<
  Record<string, { lat: number; lon: number }>
> {
  return json(await fetch(apiUrl("/api/environments/theaters")));
}

// ---- Ingestion ----

export async function ingestDocument(
  file: File,
  autoSolve = true
): Promise<{
  alert_id: number;
  document_name: string;
  extracted: Record<string, unknown>;
  confidence: number;
  mission_id?: number;
  message: string;
}> {
  const fd = new FormData();
  fd.append("file", file);
  return json(
    await fetch(apiUrl(`/api/ingest?auto_solve=${autoSolve}`), {
      method: "POST",
      body: fd,
    })
  );
}

// ---- Alerts ----

export async function listAlerts(status?: string): Promise<Alert[]> {
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  return json(await fetch(apiUrl(`/api/alerts?${params}`)));
}

export async function dismissAlert(id: number): Promise<void> {
  await fetch(apiUrl(`/api/alerts/${id}/dismiss`), { method: "POST" });
}

// ---- WebSocket ----

export function connectWS(
  onEvent: (event: string, payload: Record<string, unknown>) => void
): WebSocket {
  const fallbackProto = window.location.protocol === "https:" ? "wss" : "ws";
  const fallbackWsUrl = `${fallbackProto}://${window.location.host}/ws`;
  const ws = new WebSocket(WS_URL || fallbackWsUrl);
  ws.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data);
      onEvent(data.event, data.payload);
    } catch {
      /* ignore malformed */
    }
  };
  return ws;
}
