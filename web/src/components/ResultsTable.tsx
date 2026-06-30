"use client";

import { downloadCsv } from "@/lib/csv";
import { getPrimaryResult } from "@/lib/plot";
import type { PlotField, RunSqlResponse } from "@/lib/types";

interface ResultsTableProps {
  result: RunSqlResponse | null;
  columnConfig?: PlotField[];
}

export function ResultsTable({ result, columnConfig }: ResultsTableProps) {
  const primary = getPrimaryResult(result);
  if (!primary || !primary.columns?.length) {
    return (
      <p className="text-sm text-slate-400">No tabular data to display.</p>
    );
  }

  const allColumns = primary.columns;
  // Optional column projection from a "table" plot_config.
  const hasConfig = Array.isArray(columnConfig) && columnConfig.length > 0;
  const indices = hasConfig
    ? columnConfig!
        .map((c) => allColumns.indexOf(c.value))
        .filter((i) => i >= 0)
    : allColumns.map((_, i) => i);
  const headers = hasConfig
    ? indices.map((i, k) => columnConfig![k]?.name ?? allColumns[i])
    : allColumns;

  const rowCount = primary.row_count ?? primary.rows.length;

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wide text-slate-400">
          {rowCount} row{rowCount === 1 ? "" : "s"}
        </span>
        <button
          onClick={() => downloadCsv(allColumns, primary.rows)}
          className="inline-flex items-center gap-1.5 rounded-md border border-slate-200 px-2.5 py-1 text-xs font-medium text-slate-600 transition hover:border-slate-300 hover:bg-slate-50"
        >
          <svg className="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
            <path d="M10 12.5l-3.5-3.5h2.25V3h2.5v6h2.25L10 12.5z" />
            <path d="M4 14.5h12V16H4z" />
          </svg>
          Download CSV
        </button>
      </div>
      <div className="max-h-[380px] overflow-auto rounded-lg border border-slate-200">
        <table className="w-full border-collapse text-left text-sm">
          <thead className="sticky top-0 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              {headers.map((h, i) => (
                <th key={i} className="whitespace-nowrap px-3 py-2 font-semibold">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {primary.rows.map((row, ri) => (
              <tr key={ri} className="hover:bg-slate-50/70">
                {indices.map((ci) => (
                  <td key={ci} className="whitespace-nowrap px-3 py-1.5 text-slate-700">
                    {row[ci] === null || row[ci] === undefined ? "" : String(row[ci])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
