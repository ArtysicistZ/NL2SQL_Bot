"use client";

import { useCallback, useRef, useState } from "react";

import { api } from "@/lib/api";
import {
  ApiError,
  type HistoryEntry,
  type PlotConfig,
  type RunSqlResponse,
} from "@/lib/types";

export type Phase = "idle" | "asking" | "running" | "done" | "error";

export interface CurrentResult {
  question: string;
  answer: string;
  sql: string;
  plotConfig: PlotConfig;
  result: RunSqlResponse | null;
}

function newId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.floor(Math.random() * 1e6)}`;
}

export function useNl2Sql() {
  const [question, setQuestion] = useState("");
  const [phase, setPhase] = useState<Phase>("idle");
  const [error, setError] = useState<string | null>(null);
  const [current, setCurrent] = useState<CurrentResult | null>(null);
  const [editedSql, setEditedSql] = useState("");
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [rerunning, setRerunning] = useState(false);
  const [rerunError, setRerunError] = useState<string | null>(null);

  const abortRef = useRef<AbortController | null>(null);

  const ask = useCallback(async (raw?: string) => {
    const q = (raw ?? question).trim();
    if (!q) {
      setError("Enter a question to continue.");
      setPhase("error");
      return;
    }
    // Cancel any in-flight request so a new question wins.
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setError(null);
    setRerunError(null);
    setPhase("asking");
    setCurrent(null);

    try {
      const ask = await api.ask(q, controller.signal);
      setPhase("running");
      setEditedSql(ask.sql);

      let result: RunSqlResponse | null = null;
      if (ask.sql) {
        try {
          result = await api.runSql(ask.sql, controller.signal);
        } catch (err) {
          if (err instanceof DOMException && err.name === "AbortError") return;
          // Keep the answer even if charting the SQL fails.
          result = null;
        }
      }

      if (controller.signal.aborted) return;

      const resolved: CurrentResult = {
        question: q,
        answer: ask.answer,
        sql: ask.sql,
        plotConfig: ask.plot_config,
        result,
      };
      setCurrent(resolved);
      setHistory((h) => [
        { id: newId(), question: q, answer: ask.answer, sql: ask.sql, plotConfig: ask.plot_config, result },
        ...h,
      ]);
      setPhase("done");
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return;
      const message = err instanceof ApiError ? err.message : "Something went wrong.";
      setError(message);
      setPhase("error");
    }
  }, [question]);

  const rerunSql = useCallback(async () => {
    const sql = editedSql.trim();
    if (!sql || !current) return;
    setRerunning(true);
    setRerunError(null);
    try {
      const result = await api.runSql(sql);
      setCurrent({ ...current, sql, result });
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Failed to run SQL.";
      setRerunError(message);
    } finally {
      setRerunning(false);
    }
  }, [editedSql, current]);

  const restore = useCallback((entry: HistoryEntry) => {
    setQuestion(entry.question);
    setEditedSql(entry.sql);
    setCurrent({
      question: entry.question,
      answer: entry.answer,
      sql: entry.sql,
      plotConfig: entry.plotConfig,
      result: entry.result,
    });
    setPhase("done");
    setError(null);
    setRerunError(null);
  }, []);

  const dismissError = useCallback(() => setError(null), []);

  return {
    question,
    setQuestion,
    phase,
    error,
    current,
    editedSql,
    setEditedSql,
    history,
    rerunning,
    rerunError,
    ask,
    rerunSql,
    restore,
    dismissError,
  };
}
