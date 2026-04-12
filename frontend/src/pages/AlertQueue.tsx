import { useEffect } from "react";
import { Link } from "react-router-dom";
import { useMissionStore } from "../store/missionStore";
import * as api from "../api/client";

export default function AlertQueue() {
  const { alerts, fetchAlerts } = useMissionStore();

  useEffect(() => {
    fetchAlerts();
  }, []);

  async function handleDismiss(id: number) {
    await api.dismissAlert(id);
    fetchAlerts();
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-cyan-400">Alert Queue</h1>
      <p className="text-sm text-gray-400">
        Incoming alerts from ingested documents. Each processed alert
        generates a mission for review.
      </p>

      {alerts.length === 0 ? (
        <div className="glass-card flex h-48 items-center justify-center text-gray-500">
          No alerts yet. Upload a document to generate alerts.
        </div>
      ) : (
        <div className="space-y-3">
          {alerts.map((alert) => (
            <div key={alert.id} className="glass-card-hover">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <div className="flex items-center gap-3">
                    <h3 className="font-medium text-gray-200">
                      {alert.document_name}
                    </h3>
                    <span
                      className={`status-badge ${
                        alert.status === "processed"
                          ? "bg-green-500/10 text-green-400"
                          : alert.status === "dismissed"
                            ? "bg-gray-500/10 text-gray-500"
                            : "bg-yellow-500/10 text-yellow-400"
                      }`}
                    >
                      {alert.status}
                    </span>
                    {alert.confidence != null && (
                      <span className="text-xs text-gray-500">
                        {(alert.confidence * 100).toFixed(0)}% confidence
                      </span>
                    )}
                  </div>

                  {/* Extracted highlights */}
                  <div className="flex flex-wrap gap-2 text-xs">
                    {alert.extracted.location_name && (
                      <span className="rounded bg-white/5 px-2 py-0.5 text-gray-300">
                        {String(alert.extracted.location_name)}
                      </span>
                    )}
                    {alert.extracted.survivors_estimate && (
                      <span className="rounded bg-red-500/10 px-2 py-0.5 text-red-300">
                        {String(alert.extracted.survivors_estimate)} survivors
                      </span>
                    )}
                    {alert.extracted.urgency && (
                      <span className="rounded bg-yellow-500/10 px-2 py-0.5 text-yellow-300">
                        {String(alert.extracted.urgency)}
                      </span>
                    )}
                  </div>

                  <p className="text-xs text-gray-500">
                    Created{" "}
                    {alert.created_at
                      ? new Date(alert.created_at).toLocaleString()
                      : "unknown"}
                  </p>
                </div>

                <div className="flex gap-2">
                  {alert.mission_id && (
                    <Link
                      to="/review"
                      className="rounded-lg border border-cyan-500/20 bg-cyan-500/10 px-3 py-1 text-xs text-cyan-400"
                    >
                      Mission #{alert.mission_id}
                    </Link>
                  )}
                  {alert.status !== "dismissed" && (
                    <button
                      className="rounded-lg border border-red-500/20 bg-red-500/10 px-3 py-1 text-xs text-red-400"
                      onClick={() => handleDismiss(alert.id)}
                    >
                      Dismiss
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
