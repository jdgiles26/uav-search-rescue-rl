import { useEffect } from "react";
import { Link } from "react-router-dom";
import { useMissionStore } from "../store/missionStore";
import { STATUS_COLORS } from "../types";

export default function Dashboard() {
  const { missions, alerts, fetchMissions, fetchAlerts } = useMissionStore();

  useEffect(() => {
    fetchMissions();
    fetchAlerts();
  }, []);

  const pending = missions.filter((m) => m.status === "pending_review");
  const active = missions.filter((m) => m.status === "active");
  const totalReward = missions.reduce(
    (s, m) => s + (m.total_reward ?? 0),
    0
  );

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-cyan-400">
        Command Dashboard
      </h1>

      {/* Metric cards */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: "Total Missions", value: missions.length, color: "text-gray-100" },
          { label: "Pending Review", value: pending.length, color: "text-yellow-400" },
          { label: "Active Missions", value: active.length, color: "text-cyan-400" },
          { label: "Alerts", value: alerts.length, color: "text-red-400" },
        ].map((card) => (
          <div key={card.label} className="glass-card">
            <p className="text-xs uppercase tracking-wider text-gray-500">
              {card.label}
            </p>
            <p className={`mt-1 text-3xl font-bold ${card.color}`}>
              {card.value}
            </p>
          </div>
        ))}
      </div>

      {/* Quick actions */}
      <div className="flex gap-3">
        <Link to="/planner" className="btn-primary">
          New Manual Mission
        </Link>
        <Link to="/ingest" className="btn-primary">
          Upload Document
        </Link>
        {pending.length > 0 && (
          <Link to="/review" className="btn-primary">
            Review {pending.length} Pending
          </Link>
        )}
      </div>

      {/* Recent missions table */}
      <div className="glass-card">
        <h2 className="mb-4 text-lg font-medium text-gray-200">
          Recent Missions
        </h2>
        {missions.length === 0 ? (
          <p className="text-sm text-gray-500">
            No missions yet. Create one from the Mission Planner or upload a document.
          </p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/5 text-left text-xs uppercase tracking-wider text-gray-500">
                <th className="pb-2">ID</th>
                <th className="pb-2">Name</th>
                <th className="pb-2">Status</th>
                <th className="pb-2">Source</th>
                <th className="pb-2">Algorithm</th>
                <th className="pb-2">Reward</th>
                <th className="pb-2">Created</th>
              </tr>
            </thead>
            <tbody>
              {missions.slice(0, 15).map((m) => (
                <tr
                  key={m.id}
                  className="border-b border-white/[0.03] hover:bg-white/[0.02]"
                >
                  <td className="py-2 font-mono text-gray-400">#{m.id}</td>
                  <td className="py-2">{m.name}</td>
                  <td className="py-2">
                    <span
                      className={`status-badge ${
                        STATUS_COLORS[m.status] ?? "text-gray-400"
                      } bg-current/10`}
                    >
                      {m.status.replace("_", " ")}
                    </span>
                  </td>
                  <td className="py-2 text-gray-400">{m.source}</td>
                  <td className="py-2 font-mono text-gray-400">
                    {m.algorithm ?? "-"}
                  </td>
                  <td className="py-2 font-mono text-cyan-400">
                    {m.total_reward?.toFixed(0) ?? "-"}
                  </td>
                  <td className="py-2 text-gray-500">
                    {m.created_at
                      ? new Date(m.created_at).toLocaleDateString()
                      : "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Recent alerts */}
      {alerts.length > 0 && (
        <div className="glass-card">
          <h2 className="mb-4 text-lg font-medium text-gray-200">
            Recent Alerts
          </h2>
          <div className="space-y-2">
            {alerts.slice(0, 5).map((a) => (
              <div
                key={a.id}
                className="flex items-center justify-between rounded-lg border border-white/5 bg-white/[0.02] px-4 py-2"
              >
                <div>
                  <span className="font-medium">{a.document_name}</span>
                  <span className="ml-3 text-xs text-gray-500">
                    Confidence: {((a.confidence ?? 0) * 100).toFixed(0)}%
                  </span>
                </div>
                <span
                  className={`status-badge ${
                    a.status === "processed"
                      ? "text-green-400"
                      : "text-yellow-400"
                  }`}
                >
                  {a.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
