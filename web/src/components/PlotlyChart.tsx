"use client";

import Plotly from "plotly.js-dist-min";
import type { Data, Layout } from "plotly.js-dist-min";
import createPlotlyComponent from "react-plotly.js/factory";

// Build the React wrapper from the slim Plotly bundle (keeps the chunk small).
const Plot = createPlotlyComponent(Plotly);

interface PlotlyChartProps {
  traces: Data[];
  layout: Partial<Layout>;
}

export default function PlotlyChart({ traces, layout }: PlotlyChartProps) {
  return (
    <Plot
      data={traces}
      layout={layout}
      useResizeHandler
      style={{ width: "100%", height: "100%" }}
      config={{ displayModeBar: false, responsive: true }}
    />
  );
}
