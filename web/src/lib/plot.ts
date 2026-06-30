// Pure, framework-free translation of plot_config + SQL rows into Plotly
// traces/layout (ported and cleaned from the legacy frontend/app.js).
import type { Data, Layout } from "plotly.js-dist-min";

import type { PlotConfig, ResultSet, RunSqlResponse } from "@/lib/types";

export type PlotOutcome =
  | { mode: "chart"; traces: Data[]; layout: Partial<Layout> }
  | { mode: "table" }
  | { mode: "message"; message: string; isError?: boolean };

type Row = Record<string, unknown>;

/** Zip positional rows against columns into objects keyed by column name. */
export function rowsToObjects(columns: string[], rows: unknown[][]): Row[] {
  return rows.map((row) => {
    const obj: Row = {};
    columns.forEach((col, idx) => {
      obj[col] = row[idx];
    });
    return obj;
  });
}

export function getPrimaryResult(
  result: RunSqlResponse | null,
): ResultSet | RunSqlResponse | null {
  if (!result) return null;
  if (Array.isArray(result.result_sets) && result.result_sets.length > 0) {
    return result.result_sets[0];
  }
  return result;
}

export function buildPlot(
  plotConfig: PlotConfig | null | undefined,
  result: RunSqlResponse | null,
): PlotOutcome {
  if (!plotConfig || !plotConfig.type) {
    return { mode: "message", message: "No chart configuration available." };
  }
  if (plotConfig.type === "none") {
    return {
      mode: "message",
      message: plotConfig.reason || "No chart suggested for this result.",
    };
  }
  if (plotConfig.type === "error") {
    return {
      mode: "message",
      message: plotConfig.reason || "The model could not build a chart.",
      isError: true,
    };
  }

  const primary = getPrimaryResult(result);
  if (!primary || !Array.isArray(primary.columns) || !Array.isArray(primary.rows)) {
    return { mode: "message", message: "No data available for charting." };
  }

  const rows = rowsToObjects(primary.columns, primary.rows);
  if (rows.length === 0) {
    return { mode: "message", message: "Query returned no rows." };
  }

  if (plotConfig.type === "table") {
    return { mode: "table" };
  }

  const axis = plotConfig.axis || {};
  const xField = axis.x?.value;
  const yField = axis.y?.value;
  const seriesField = axis.series?.value;

  if (!yField || (plotConfig.type !== "pie" && !xField)) {
    return {
      mode: "message",
      message: "Chart configuration is missing axis fields.",
      isError: true,
    };
  }

  const traces: Data[] = [];

  if (plotConfig.type === "pie") {
    const labelField = seriesField || xField;
    if (!labelField) {
      return {
        mode: "message",
        message: "Pie chart is missing a category field.",
        isError: true,
      };
    }
    traces.push({
      type: "pie",
      labels: rows.map((r) => String(r[labelField] ?? "")),
      values: rows.map((r) => Number(r[yField] ?? 0)),
      textinfo: "label+percent",
      hoverinfo: "label+value+percent",
      hole: 0.35,
    });
  } else {
    // Drop a degenerate series that splits every category into its own
    // single-point group (1:1 with x) — it produces an unreadable legend.
    const useSeries =
      seriesField &&
      new Set(rows.map((r) => String(r[seriesField]))).size < rows.length;
    const groups = useSeries
      ? Array.from(new Set(rows.map((r) => String(r[seriesField!]))))
      : [null];

    for (const group of groups) {
      const groupRows =
        group === null
          ? rows
          : rows.filter((r) => String(r[seriesField!]) === group);
      const name = group === null ? axis.y?.name || yField : String(group);
      const categories = groupRows.map((r) => r[xField!] as string | number);
      const values = groupRows.map((r) => Number(r[yField] ?? 0));

      if (plotConfig.type === "line") {
        traces.push({ type: "scatter", mode: "lines+markers", name, x: categories, y: values });
      } else if (plotConfig.type === "bar") {
        // Horizontal bars — good for long category labels.
        traces.push({ type: "bar", orientation: "h", name, x: values, y: categories });
      } else {
        // "column" (and any other) — vertical bars.
        traces.push({ type: "bar", name, x: categories, y: values });
      }
    }
  }

  const layout: Partial<Layout> = {
    title: plotConfig.title ? { text: plotConfig.title } : undefined,
    margin: { t: plotConfig.title ? 48 : 24, l: 56, r: 24, b: 56 },
    legend: { orientation: "h" },
    autosize: true,
    font: { family: "Inter, ui-sans-serif, system-ui, sans-serif", size: 12 },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    colorway: ["#6366f1", "#0ea5e9", "#22c55e", "#f59e0b", "#ef4444", "#a855f7", "#14b8a6"],
  };

  return { mode: "chart", traces, layout };
}
