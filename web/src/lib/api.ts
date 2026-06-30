// The single place that knows backend URLs. The browser calls same-origin
// /api/*, which next.config.mjs rewrites to the FastAPI backend.
import {
  ApiError,
  type AskResponse,
  type RunSqlResponse,
} from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "/api";

async function postJson<T>(
  path: string,
  body: unknown,
  signal?: AbortSignal,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal,
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    throw new ApiError(
      "Could not reach the server. Is the backend running?",
      0,
    );
  }

  if (!response.ok) {
    // FastAPI errors come back as { detail: "..." }.
    let detail = `Request failed (${response.status}).`;
    try {
      const data = await response.json();
      if (data && typeof data.detail === "string") detail = data.detail;
    } catch {
      const text = await response.text().catch(() => "");
      if (text) detail = text;
    }
    throw new ApiError(detail, response.status);
  }

  return (await response.json()) as T;
}

export const api = {
  ask(question: string, signal?: AbortSignal): Promise<AskResponse> {
    return postJson<AskResponse>("/ask", { question }, signal);
  },
  runSql(sql: string, signal?: AbortSignal): Promise<RunSqlResponse> {
    return postJson<RunSqlResponse>("/run_sql", { sql }, signal);
  },
};
