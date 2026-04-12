export interface Node {
  id: number;
  x: number;
  y: number;
  reward: number;
  node_type: "depot" | "service" | "charging" | "destination";
  lat?: number;
  lon?: number;
}

export interface Route {
  uav_index: number;
  node_ids: number[];
  reward: number;
  distance_km: number;
}

export interface EnvironmentConfig {
  n_service_nodes: number;
  n_charging_stations: number;
  map_size: number;
  time_limit: number;
  battery_limit: number;
  seed: number;
  n_uavs?: number;
}

export interface Solution {
  algorithm: string;
  routes: Route[];
  total_reward: number;
  solve_time_s: number;
  cluster_assignments?: number[];
}

export interface Mission {
  id: number;
  name: string;
  status:
    | "draft"
    | "pending_review"
    | "approved"
    | "active"
    | "completed"
    | "rejected";
  theater: string;
  theater_lat: number;
  theater_lon: number;
  source: "manual" | "auto_ingest";
  algorithm?: string;
  total_reward?: number;
  solve_time_s?: number;
  config: EnvironmentConfig;
  solution?: Solution;
  created_at?: string;
  updated_at?: string;
  alert_id?: number;
}

export interface Alert {
  id: number;
  document_name: string;
  status: "new" | "processing" | "processed" | "failed" | "dismissed";
  extracted: Record<string, unknown>;
  confidence?: number;
  mission_id?: number;
  created_at?: string;
  processed_at?: string;
}

export interface WSEvent {
  event: string;
  payload: Record<string, unknown>;
}

export const ROUTE_COLORS = [
  "#00d4ff",
  "#ff3366",
  "#00ff88",
  "#ffaa00",
  "#aa55ff",
  "#ff6633",
  "#33ffcc",
  "#ff33cc",
];

export const STATUS_COLORS: Record<string, string> = {
  draft: "text-gray-400",
  pending_review: "text-yellow-400",
  approved: "text-green-400",
  active: "text-cyber-500",
  completed: "text-emerald-400",
  rejected: "text-red-400",
};
