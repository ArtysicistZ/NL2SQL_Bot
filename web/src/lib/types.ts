// Types mirroring the FastAPI contract (app/api.py, app/schemas.py).

export interface AskRequest {
  question: string;
}

export interface RunSqlRequest {
  sql: string;
}

/** A column/value mapping used by plot_config (name = label, value = SQL alias). */
export interface PlotField {
  name: string;
  value: string;
}

export type PlotType =
  | "none"
  | "error"
  | "table"
  | "bar"
  | "column"
  | "line"
  | "pie";

/**
 * plot_config is produced by the LLM, so every field below is optional and
 * must be treated defensively. The backend only guarantees the top-level keys
 * of AskResponse, not the shape of plot_config.
 */
export interface PlotConfig {
  type: PlotType;
  title?: string;
  reason?: string;
  axis?: {
    x?: PlotField;
    y?: PlotField;
    series?: PlotField;
  };
  columns?: PlotField[];
}

export interface AskResponse {
  answer: string;
  plot_config: PlotConfig;
  sql: string;
}

/**
 * IMPORTANT: `rows` is an array of positional arrays aligned to `columns`
 * (rows[i][j] corresponds to columns[j]) — NOT an array of objects.
 */
export interface ResultSet {
  sql: string;
  columns: string[];
  rows: unknown[][];
  row_count: number;
}

export interface RunSqlResponse {
  status: "success";
  sql: string;
  columns: string[];
  rows: unknown[][];
  row_count: number;
  result_sets: ResultSet[];
}

/** Thrown by the API client on any non-2xx response. */
export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/** One entry in the in-session query history. */
export interface HistoryEntry {
  id: string;
  question: string;
  answer: string;
  sql: string;
  plotConfig: PlotConfig;
  result: RunSqlResponse | null;
}
