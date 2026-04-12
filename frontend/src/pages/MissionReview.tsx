import { useEffect, useState } from "react";
import { useMissionStore } from "../store/missionStore";
import * as api from "../api/client";
import MissionMap from "../components/MissionMap";
import RewardChart from "../components/RewardChart";
import type { Mission } from "../types";

export default function MissionReview() {
  const { missions, fetchMissions } = useMissionStore();
  const [selected, setSelected] = useState<Mission | null>(null);
  const [reviewNotes, setReviewNotes] = useState("");
  const [reviewer, setReviewer] = useState("analyst");

  useEffect(() => {
    fetchMissions();
  }, []);

  const pending = missions.filter((m) => m.status === "pending_review");
  const recent = missions.filter(
    (m) => m.status === "approved" || m.status === "rejected"
  );

  async function handleReview(action: "approve" | "reject") {
    if (!selected) return;
    await api.reviewMission(selected.id, action, reviewer, reviewNotes);
    setSelected(null);
    setReviewNotes("");
    fetchMissions();
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-cyan-400">Mission Review</h1>

      <div className="grid grid-cols-12 gap-6">
        {/* Left: Queue */}
        <div className="col-span-4 space-y-4">
          <div className="glass-card">
            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-yellow-400">
              Pending Review ({pending.length})
            </h3>
            {pending.length === 0 ? (
              <p className="text-sm text-gray-500">No missions pending review.</p>
            ) : (
              <div className="space-y-2">
                {pending.map((m) => (
                  <button
                    key={m.id}
                    onClick={() => setSelected(m)}
                    className={`w-full rounded-lg border px-3 py-2 text-left transition-colors ${
                      selected?.id === m.id
                        ? "border-cyan-500/40 bg-cyan-500/10"
                        : "border-white/5 bg-white/[0.02] hover:border-white/10"
                    }`}
                  >
                    <p className="text-sm font-medium text-gray-200">
                      {m.name}
                    </p>
                    <div className="mt-1 flex items-center gap-2 text-xs text-gray-500">
                      <span>{m.theater}</span>
                      {m.total_reward != null && (
                        <span className="text-cyan-400">
                          R: {m.total_reward.toFixed(0)}
                        </span>
                      )}
                      <span>{m.source}</span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Recent reviews */}
          {recent.length > 0 && (
            <div className="glass-card">
              <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-gray-400">
                Recent Reviews
              </h3>
              <div className="space-y-1">
                {recent.slice(0, 5).map((m) => (
                  <div
                    key={m.id}
                    className="flex items-center justify-between rounded px-2 py-1 text-xs"
                  >
                    <span className="text-gray-400">{m.name}</span>
                    <span
                      className={
                        m.status === "approved"
                          ? "text-green-400"
                          : "text-red-400"
                      }
                    >
                      {m.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right: Detail */}
        <div className="col-span-8 space-y-4">
          {!selected ? (
            <div className="glass-card flex h-96 items-center justify-center text-gray-500">
              Select a pending mission to review.
            </div>
          ) : (
            <>
              {/* Mission info */}
              <div className="glass-card">
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="text-lg font-medium text-gray-200">
                      {selected.name}
                    </h2>
                    <p className="text-sm text-gray-400">
                      {selected.theater} | Source: {selected.source} |
                      Algorithm: {selected.algorithm ?? "pending"}
                    </p>
                  </div>
                  <span className="status-badge bg-yellow-500/10 text-yellow-400">
                    pending review
                  </span>
                </div>

                {/* Config summary */}
                <div className="mt-3 grid grid-cols-4 gap-3 text-sm">
                  {[
                    ["Survivors", selected.config.n_service_nodes],
                    ["UAVs", selected.config.n_uavs ?? "?"],
                    ["Battery", selected.config.battery_limit],
                    ["Time Limit", selected.config.time_limit],
                  ].map(([label, val]) => (
                    <div key={String(label)}>
                      <span className="text-xs text-gray-500">{label}</span>
                      <p className="font-mono text-gray-200">{String(val)}</p>
                    </div>
                  ))}
                </div>

                {/* Solution summary */}
                {selected.solution && (
                  <div className="mt-3 grid grid-cols-3 gap-3 border-t border-white/5 pt-3 text-sm">
                    <div>
                      <span className="text-xs text-gray-500">
                        Total Reward
                      </span>
                      <p className="text-lg font-bold text-cyan-400">
                        {selected.total_reward?.toFixed(0)}
                      </p>
                    </div>
                    <div>
                      <span className="text-xs text-gray-500">Routes</span>
                      <p className="text-gray-200">
                        {selected.solution.routes.length} UAVs
                      </p>
                    </div>
                    <div>
                      <span className="text-xs text-gray-500">Solve Time</span>
                      <p className="text-gray-200">
                        {selected.solve_time_s?.toFixed(1)}s
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {/* Map */}
              <div className="glass-card p-0 overflow-hidden">
                <MissionMap mission={selected} height={400} />
              </div>

              {/* Analytics */}
              {selected.solution && (
                <div className="glass-card">
                  <RewardChart solution={selected.solution} />
                </div>
              )}

              {/* Review actions */}
              <div className="glass-card">
                <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-gray-400">
                  Analyst Review
                </h3>
                <div className="space-y-3">
                  <label className="block">
                    <span className="text-xs text-gray-500">Reviewer</span>
                    <input
                      className="mt-1 w-full rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-sm text-gray-200 outline-none"
                      value={reviewer}
                      onChange={(e) => setReviewer(e.target.value)}
                    />
                  </label>
                  <label className="block">
                    <span className="text-xs text-gray-500">Notes</span>
                    <textarea
                      className="mt-1 w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-gray-200 outline-none"
                      rows={3}
                      value={reviewNotes}
                      onChange={(e) => setReviewNotes(e.target.value)}
                      placeholder="Optional review notes..."
                    />
                  </label>
                  <div className="flex gap-3">
                    <button
                      className="btn-primary flex-1"
                      onClick={() => handleReview("approve")}
                    >
                      Approve Mission
                    </button>
                    <button
                      className="btn-danger flex-1"
                      onClick={() => handleReview("reject")}
                    >
                      Reject
                    </button>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
