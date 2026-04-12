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

export default function RewardChart({ solution }: { solution: Solution }) {
  const labels = solution.routes.map((_, i) => `UAV ${i + 1}`);
  const values = solution.routes.map((r) => r.reward);
  const colors = solution.routes.map(
    (_, i) => ROUTE_COLORS[i % ROUTE_COLORS.length]
  );

  return (
    <Plot
      data={[
        {
          type: "bar",
          x: labels,
          y: values,
          marker: { color: colors },
          text: values.map(String),
          textposition: "auto",
        },
      ]}
      layout={{
        title: "Reward per UAV",
        height: 380,
        ...DARK_LAYOUT,
      }}
      config={{ displayModeBar: false, responsive: true }}
      className="w-full"
    />
  );
}
