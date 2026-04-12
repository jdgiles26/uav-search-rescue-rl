import { useEffect, useRef } from "react";
import L from "leaflet";
import type { Mission, Node } from "../types";
import { ROUTE_COLORS } from "../types";

interface Props {
  mission: Mission;
  height?: number;
}

export default function MissionMap({ mission, height = 600 }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Create map
    if (mapRef.current) {
      mapRef.current.remove();
    }
    const map = L.map(containerRef.current, {
      zoomControl: true,
    }).setView([mission.theater_lat, mission.theater_lon], 13);

    L.tileLayer(
      "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
      {
        attribution: "&copy; CartoDB",
        maxZoom: 19,
      }
    ).addTo(map);

    mapRef.current = map;

    const sol = mission.solution;
    if (!sol) {
      // No solution yet — just show center marker
      L.circleMarker([mission.theater_lat, mission.theater_lon], {
        radius: 10,
        color: "#00d4ff",
        fillColor: "#00d4ff",
        fillOpacity: 0.5,
      })
        .addTo(map)
        .bindPopup("Theater of Operations");
      return;
    }

    // Build a node lookup from environment_json stored inside solution
    // The solution routes reference node IDs — we need lat/lon from the environment
    // We'll reconstruct from the mission config center + route node_ids
    // For now, we display routes as connected lines if lat/lon available

    const nodes: Node[] = [];
    // Try to get nodes from solution payload (if backend stored them)
    // Fallback: generate approximate positions from theater center
    const envData = (mission as any).environment_data;

    // Draw routes
    sol.routes.forEach((route, idx) => {
      const color = ROUTE_COLORS[idx % ROUTE_COLORS.length];

      // If we have node coordinates, draw the actual path
      // For now, create a pulsing marker at theater center per UAV
      const offset = idx * 0.002;
      const uavPos: L.LatLng = L.latLng(
        mission.theater_lat + offset,
        mission.theater_lon + offset
      );

      L.circleMarker(uavPos, {
        radius: 8,
        color,
        fillColor: color,
        fillOpacity: 0.7,
      })
        .addTo(map)
        .bindPopup(
          `<b>UAV ${idx + 1}</b><br/>` +
            `Waypoints: ${route.node_ids.length}<br/>` +
            `Reward: ${route.reward}<br/>` +
            `Distance: ${route.distance_km.toFixed(3)} km`
        );
    });

    // Depot marker
    L.marker([mission.theater_lat, mission.theater_lon], {
      icon: L.divIcon({
        className: "",
        html: `<div style="background:#22c55e;width:14px;height:14px;border-radius:50%;border:2px solid #fff;"></div>`,
        iconSize: [14, 14],
        iconAnchor: [7, 7],
      }),
    })
      .addTo(map)
      .bindPopup("Command Base (Depot)");

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [mission]);

  return (
    <div
      ref={containerRef}
      style={{ height, width: "100%", borderRadius: 12 }}
    />
  );
}
