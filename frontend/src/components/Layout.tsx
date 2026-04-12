import { NavLink, Outlet } from "react-router-dom";
import { useEffect, useState } from "react";
import { connectWS } from "../api/client";
import { useMissionStore } from "../store/missionStore";
import clsx from "clsx";

const NAV = [
  { to: "/", label: "Dashboard", icon: "grid" },
  { to: "/planner", label: "Mission Planner", icon: "map" },
  { to: "/ingest", label: "Document Intake", icon: "upload" },
  { to: "/alerts", label: "Alert Queue", icon: "bell" },
  { to: "/review", label: "Mission Review", icon: "check-circle" },
] as const;

const ICONS: Record<string, string> = {
  grid: "M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z",
  map: "M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7",
  upload:
    "M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12",
  bell: "M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9",
  "check-circle":
    "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z",
};

function SvgIcon({ name }: { name: string }) {
  return (
    <svg
      className="h-5 w-5 shrink-0"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={1.5}
    >
      <path strokeLinecap="round" strokeLinejoin="round" d={ICONS[name]} />
    </svg>
  );
}

export default function Layout() {
  const { fetchMissions, fetchAlerts } = useMissionStore();
  const [toast, setToast] = useState<string | null>(null);

  useEffect(() => {
    fetchMissions();
    fetchAlerts();

    const ws = connectWS((event, payload) => {
      if (event === "alert_created") {
        setToast(`New alert: ${payload.document_name}`);
        fetchAlerts();
        fetchMissions();
      } else if (event === "mission_solved") {
        setToast(
          `Mission #${payload.mission_id} solved — reward ${payload.total_reward}`
        );
        fetchMissions();
      } else if (event === "mission_reviewed") {
        fetchMissions();
      }
      setTimeout(() => setToast(null), 5000);
    });

    return () => ws.close();
  }, []);

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="flex w-56 shrink-0 flex-col border-r border-white/5 bg-[rgba(13,17,23,0.95)]">
        <div className="flex items-center gap-2 border-b border-white/5 px-5 py-4">
          <span className="text-xl">&#x1F6F0;</span>
          <span className="font-semibold tracking-tight text-cyan-400">
            UAV SAR
          </span>
        </div>

        <nav className="flex-1 space-y-1 px-3 py-4">
          {NAV.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.to === "/"}
              className={({ isActive }) =>
                clsx(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                  isActive
                    ? "bg-cyan-500/10 text-cyan-400"
                    : "text-gray-400 hover:bg-white/5 hover:text-gray-200"
                )
              }
            >
              <SvgIcon name={n.icon} />
              {n.label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-white/5 px-4 py-3 text-xs text-gray-500">
          UAV SAR Platform v1.0
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto">
        {toast && (
          <div className="sticky top-0 z-50 border-b border-cyan-500/20 bg-cyan-500/10 px-6 py-2 text-sm text-cyan-300 backdrop-blur-sm">
            {toast}
          </div>
        )}
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
