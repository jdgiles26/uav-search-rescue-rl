import { useState } from "react";
import * as api from "../api/client";
import { useMissionStore } from "../store/missionStore";
import MissionMap from "../components/MissionMap";
import RewardChart from "../components/RewardChart";
import BatteryChart from "../components/BatteryChart";
import type { Mission, EnvironmentConfig } from "../types";

const THEATERS = [
  "Sierra Nevada, CA",
  "Rocky Mountains, CO",
  "Appalachian Trail, VA",
  "Grand Canyon, AZ",
  "Olympic Peninsula, WA",
];

const ALGORITHMS = [
  { value: "improved_ql", label: "Improved Q-Learning (Reward-Biased)" },
  { value: "ql_ndts", label: "Original Q-Learning (NDTS)" },
  { value: "greedy", label: "Greedy Baseline" },
];

const EPISODE_OPTIONS = [5000, 10000, 20000, 50000, 100000];

export default function MissionPlanner() {
  const { addMission } = useMissionStore();

  // Config state
  const [name, setName] = useState("Manual Mission");
  const [theater, setTheater] = useState(THEATERS[0]);
  const [nService, setNService] = useState(20);
  const [nCharging, setNCharging] = useState(4);
  const [mapSize, setMapSize] = useState(100);
  const [timeLimit, setTimeLimit] = useState(150);
  const [batteryLimit, setBatteryLimit] = useState(80);
  const [seed, setSeed] = useState(42);
  const [nUavs, setNUavs] = useState(2);
  const [algorithm, setAlgorithm] = useState("improved_ql");
  const [nEpisodes, setNEpisodes] = useState(10000);

  // Workflow state
  const [mission, setMission] = useState<Mission | null>(null);
  const [solving, setSolving] = useState(false);
  const [tab, setTab] = useState<"map" | "analytics" | "routes">("map");

  async function handleGenerate() {
    const config: EnvironmentConfig = {
      n_service_nodes: nService,
      n_charging_stations: nCharging,
      map_size: mapSize,
      time_limit: timeLimit,
      battery_limit: batteryLimit,
      seed,
    };
    const m = await api.createMission({
      name,
      theater,
      config,
      source: "manual",
    });
    setMission(m);
    addMission(m);
  }

  async function handleSolve() {
    if (!mission) return;
    setSolving(true);
    try {
      const result = await api.solveMission({
        mission_id: mission.id,
        algorithm,
        n_uavs: nUavs,
        n_episodes: nEpisodes,
      });
      // Refresh mission with solution
      const updated = await api.getMission(mission.id);
      setMission(updated);
    } finally {
      setSolving(false);
    }
  }

  const hasSolution = !!mission?.solution;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-cyan-400">Mission Planner</h1>

      <div className="grid grid-cols-12 gap-6">
        {/* Sidebar controls */}
        <div className="col-span-3 space-y-4">
          <div className="glass-card space-y-3">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-400">
              Mission Setup
            </h3>

            <label className="block">
              <span className="text-xs text-gray-500">Mission Name</span>
              <input
                className="mt-1 w-full rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-sm text-gray-200 outline-none focus:border-cyan-500/40"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </label>

            <label className="block">
              <span className="text-xs text-gray-500">Theater</span>
              <select
                className="mt-1 w-full rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-sm text-gray-200 outline-none"
                value={theater}
                onChange={(e) => setTheater(e.target.value)}
              >
                {THEATERS.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </label>

            <div className="grid grid-cols-2 gap-2">
              {([
                ["Survivors", nService, setNService, 5, 100],
                ["Charging", nCharging, setNCharging, 1, 10],
                ["Map Size", mapSize, setMapSize, 50, 200],
                ["Time Limit", timeLimit, setTimeLimit, 50, 300],
                ["Battery", batteryLimit, setBatteryLimit, 25, 150],
                ["Seed", seed, setSeed, 0, 9999],
              ] as const).map(([label, val, setter, min, max]) => (
                <label key={label} className="block">
                  <span className="text-xs text-gray-500">{label}</span>
                  <input
                    type="number"
                    className="mt-1 w-full rounded-lg border border-white/10 bg-white/5 px-2 py-1 text-sm text-gray-200 outline-none"
                    value={val}
                    min={min}
                    max={max}
                    onChange={(e) => (setter as any)(Number(e.target.value))}
                  />
                </label>
              ))}
            </div>

            <button
              className="btn-primary w-full"
              onClick={handleGenerate}
            >
              Generate Environment
            </button>
          </div>

          {mission && (
            <div className="glass-card space-y-3">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-400">
                Solver
              </h3>

              <label className="block">
                <span className="text-xs text-gray-500">UAVs</span>
                <input
                  type="number"
                  className="mt-1 w-full rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-sm text-gray-200 outline-none"
                  value={nUavs}
                  min={1}
                  max={5}
                  onChange={(e) => setNUavs(Number(e.target.value))}
                />
              </label>

              <label className="block">
                <span className="text-xs text-gray-500">Algorithm</span>
                <select
                  className="mt-1 w-full rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-sm text-gray-200 outline-none"
                  value={algorithm}
                  onChange={(e) => setAlgorithm(e.target.value)}
                >
                  {ALGORITHMS.map((a) => (
                    <option key={a.value} value={a.value}>
                      {a.label}
                    </option>
                  ))}
                </select>
              </label>

              <label className="block">
                <span className="text-xs text-gray-500">Episodes</span>
                <select
                  className="mt-1 w-full rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-sm text-gray-200 outline-none"
                  value={nEpisodes}
                  onChange={(e) => setNEpisodes(Number(e.target.value))}
                >
                  {EPISODE_OPTIONS.map((n) => (
                    <option key={n} value={n}>
                      {n.toLocaleString()}
                    </option>
                  ))}
                </select>
              </label>

              <button
                className="btn-primary w-full"
                onClick={handleSolve}
                disabled={solving}
              >
                {solving ? "Solving..." : "Solve Mission"}
              </button>
            </div>
          )}

          {/* Solution summary */}
          {hasSolution && mission.solution && (
            <div className="glass-card space-y-2">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-400">
                Solution
              </h3>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <p className="text-xs text-gray-500">Total Reward</p>
                  <p className="text-lg font-bold text-cyan-400">
                    {mission.total_reward?.toFixed(0)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Solve Time</p>
                  <p className="text-lg font-bold text-gray-200">
                    {mission.solve_time_s?.toFixed(1)}s
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Algorithm</p>
                  <p className="font-mono text-gray-300">
                    {mission.algorithm}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Routes</p>
                  <p className="text-gray-300">
                    {mission.solution.routes.length} UAVs
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Main content area */}
        <div className="col-span-9 space-y-4">
          {!mission ? (
            <div className="glass-card flex h-96 items-center justify-center text-gray-500">
              Configure and generate an environment to begin.
            </div>
          ) : (
            <>
              {/* Tabs */}
              <div className="flex gap-1 rounded-lg bg-white/[0.02] p-1">
                {(["map", "analytics", "routes"] as const).map((t) => (
                  <button
                    key={t}
                    onClick={() => setTab(t)}
                    className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
                      tab === t
                        ? "bg-cyan-500/15 text-cyan-400"
                        : "text-gray-400 hover:text-gray-200"
                    }`}
                  >
                    {t === "map"
                      ? "Map View"
                      : t === "analytics"
                        ? "Analytics"
                        : "Route Details"}
                  </button>
                ))}
              </div>

              {tab === "map" && (
                <div className="glass-card p-0 overflow-hidden">
                  <MissionMap mission={mission} height={580} />
                </div>
              )}

              {tab === "analytics" && hasSolution && mission.solution && (
                <div className="grid grid-cols-2 gap-4">
                  <div className="glass-card">
                    <RewardChart solution={mission.solution} />
                  </div>
                  <div className="glass-card">
                    <BatteryChart solution={mission.solution} />
                  </div>
                </div>
              )}

              {tab === "routes" && hasSolution && mission.solution && (
                <div className="space-y-3">
                  {mission.solution.routes.map((route, idx) => (
                    <div key={idx} className="glass-card">
                      <h4 className="mb-2 font-medium text-gray-200">
                        UAV {idx + 1}
                      </h4>
                      <div className="grid grid-cols-4 gap-4 text-sm">
                        <div>
                          <span className="text-xs text-gray-500">
                            Waypoints
                          </span>
                          <p className="font-mono text-gray-200">
                            {route.node_ids.length}
                          </p>
                        </div>
                        <div>
                          <span className="text-xs text-gray-500">Reward</span>
                          <p className="font-mono text-cyan-400">
                            {route.reward}
                          </p>
                        </div>
                        <div>
                          <span className="text-xs text-gray-500">
                            Distance
                          </span>
                          <p className="font-mono text-gray-200">
                            {route.distance_km.toFixed(3)} km
                          </p>
                        </div>
                        <div>
                          <span className="text-xs text-gray-500">Route</span>
                          <p className="font-mono text-xs text-gray-400 truncate">
                            {route.node_ids.join(" -> ")}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {tab !== "map" && !hasSolution && (
                <div className="glass-card flex h-64 items-center justify-center text-gray-500">
                  Solve the mission to see {tab}.
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
