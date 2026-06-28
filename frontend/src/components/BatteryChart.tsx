import Plot from "react-plotly.js";
import type { Solution } from "../types";
import { ROUTE_COLORS } from "../types";

const DARK_LAYOUT: Partial<Plotly.Layout> = {
  paper_bgcolor: "rgba(0,0,0,0)",
  plot_bgcolor: "rgba(17,24,39,0.8)",
  font: { color: "#94a3b8", family: "Inter, sans-serif" },
  margin: { l: 40, r: 20, t: 50, b: 40 },
  xaxis: { gridcolor: "rgba(0,212,255,0.06)", zerolinecolor: "rgba(0,212,255,0.1)" },
  yaxis: { gridcolor: "rgba(0,212,255,0.06)", zerolinecolor: "rgba(0,212,255,0.1)" },
};

export default function BatteryChart({ solution }: { solution: Solution }) {
  const traces = solution.routes.map((route, idx) => ({
    type: "scatter" as const,
    mode: "lines+markers" as const,
    name: `UAV ${idx + 1}`,
    x: route.node_ids.map((_, i) => i),
    y: route.node_ids.map(() => Math.random() * 40 + 40), // placeholder until real battery data piped through
    line: { color: ROUTE_COLORS[idx % ROUTE_COLORS.length], width: 2 },
    marker: { size: 4 },
  }));

  return (
    <Plot
      data={traces}
      layout={{
        title: { text: "Route Length Comparison" },
        height: 380,
        ...DARK_LAYOUT,
        xaxis: {
          ...DARK_LAYOUT.xaxis,
          title: { text: "Step" },
        },
        yaxis: {
          ...DARK_LAYOUT.yaxis,
          title: { text: "Battery Level" },
        },
      }}
      config={{ displayModeBar: false, responsive: true }}
      className="w-full"
    />
  );
}
