"use client";

import dynamic from "next/dynamic";

import { Skeleton } from "@/components/Skeleton";
import { buildPlot } from "@/lib/plot";
import type { PlotConfig, RunSqlResponse } from "@/lib/types";

// Plotly touches `window`, so it must never render on the server.
const PlotlyChart = dynamic(() => import("@/components/PlotlyChart"), {
  ssr: false,
  loading: () => <Skeleton className="h-full w-full" />,
});

interface ChartViewProps {
  plotConfig: PlotConfig | null | undefined;
  result: RunSqlResponse | null;
}

export function ChartView({ plotConfig, result }: ChartViewProps) {
  const outcome = buildPlot(plotConfig, result);

  if (outcome.mode === "chart") {
    return (
      <div className="h-[360px] w-full">
        <PlotlyChart traces={outcome.traces} layout={outcome.layout} />
      </div>
    );
  }

  if (outcome.mode === "table") {
    // A "table" plot_config means: render the grid, not a chart.
    return (
      <p className="text-sm text-slate-400">
        This result is best viewed as a table — see the results below.
      </p>
    );
  }

  return (
    <div
      className={`flex h-[120px] items-center justify-center rounded-lg border border-dashed px-4 text-center text-sm ${
        outcome.isError
          ? "border-amber-200 bg-amber-50 text-amber-700"
          : "border-slate-200 bg-slate-50 text-slate-500"
      }`}
    >
      {outcome.message}
    </div>
  );
}
