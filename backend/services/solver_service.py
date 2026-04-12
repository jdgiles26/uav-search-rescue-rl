"""Wraps existing RL algorithms behind a uniform interface."""

from __future__ import annotations

import math
import time
from dataclasses import asdict

import backend.config  # noqa: F401  — ensures PROJECT_ROOT is on sys.path

from uav_environment import UAVEnvironment
from two_phase_cfqs import TwoPhaseApproach
from greedy_baseline import GreedySolver


KM_PER_UNIT = 0.1  # 1 map unit = 100 m


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _xy_to_latlon(x, y, map_size, center_lat, center_lon):
    cx, cy = map_size / 2, map_size / 2
    dx_km = (x - cx) * KM_PER_UNIT
    dy_km = (y - cy) * KM_PER_UNIT
    lat = center_lat + (dy_km / 111.32)
    lon = center_lon + (dx_km / (111.32 * math.cos(math.radians(center_lat))))
    return lat, lon


def _route_distance_km(env, route, center_lat, center_lon):
    total = 0.0
    for i in range(len(route) - 1):
        n1, n2 = env.nodes[route[i]], env.nodes[route[i + 1]]
        lat1, lon1 = _xy_to_latlon(n1.x, n1.y, env.map_size, center_lat, center_lon)
        lat2, lon2 = _xy_to_latlon(n2.x, n2.y, env.map_size, center_lat, center_lon)
        total += _haversine(lat1, lon1, lat2, lon2)
    return total


def serialize_environment(env: UAVEnvironment, center_lat: float, center_lon: float) -> dict:
    """Convert UAVEnvironment to a JSON-safe dict."""
    nodes = []
    for n in env.nodes:
        lat, lon = _xy_to_latlon(n.x, n.y, env.map_size, center_lat, center_lon)
        nodes.append({
            "id": n.id,
            "x": n.x,
            "y": n.y,
            "reward": n.reward,
            "node_type": n.node_type,
            "lat": lat,
            "lon": lon,
        })
    return {
        "nodes": nodes,
        "map_size": env.map_size,
        "time_limit": env.time_limit,
        "battery_limit": env.battery_limit,
        "n_service_nodes": len(env.service_nodes),
        "n_charging_stations": len(env.charging_stations),
        "distance_matrix": env.distance_matrix.tolist(),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_environment(config: dict) -> UAVEnvironment:
    return UAVEnvironment(
        n_service_nodes=config.get("n_service_nodes", 20),
        n_charging_stations=config.get("n_charging_stations", 4),
        map_size=config.get("map_size", 100),
        time_limit=config.get("time_limit", 150),
        battery_limit=config.get("battery_limit", 80),
        seed=config.get("seed", 42),
    )


def solve(
    env: UAVEnvironment,
    algorithm: str,
    n_uavs: int,
    n_episodes: int,
    center_lat: float,
    center_lon: float,
) -> dict:
    """
    Run the selected algorithm and return a standardised result dict.

    Returns
    -------
    dict with keys: algorithm, routes, total_reward, solve_time_s,
                    cluster_assignments (if applicable)
    """
    t0 = time.time()

    if algorithm == "greedy":
        solver = GreedySolver(env)
        routes, total_reward = solver.solve_multi_uav(n_uavs)
        cluster_assignments = None
    else:
        cfqs = TwoPhaseApproach(env, n_uavs=n_uavs)
        cfqs.phase1_clustering()

        if algorithm == "improved_ql":
            cfqs.phase2_solve_clusters_improved(n_episodes=n_episodes)
        else:  # ql_ndts
            cfqs.phase2_solve_clusters(n_episodes=n_episodes)

        routes = cfqs.routes
        summary = cfqs.get_solution_summary()
        total_reward = summary["total_reward"]
        cluster_assignments = (
            cfqs.cluster_assignments.tolist()
            if hasattr(cfqs, "cluster_assignments") and cfqs.cluster_assignments is not None
            else None
        )

    solve_time = time.time() - t0

    route_details = []
    for idx, route in enumerate(routes):
        reward = sum(
            env.nodes[nid].reward
            for nid in route
            if env.nodes[nid].node_type == "service"
        )
        dist = _route_distance_km(env, route, center_lat, center_lon)
        route_details.append({
            "uav_index": idx,
            "node_ids": route,
            "reward": reward,
            "distance_km": round(dist, 4),
        })

    return {
        "algorithm": algorithm,
        "routes": route_details,
        "total_reward": total_reward,
        "solve_time_s": round(solve_time, 3),
        "cluster_assignments": cluster_assignments,
    }
