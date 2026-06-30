"use client";

import type { HistoryEntry } from "@/lib/types";

interface HistoryPanelProps {
  history: HistoryEntry[];
  onRestore: (entry: HistoryEntry) => void;
  activeQuestion?: string;
}

export function HistoryPanel({ history, onRestore, activeQuestion }: HistoryPanelProps) {
  return (
    <aside className="self-start rounded-xl border border-slate-200 bg-white p-5 shadow-sm lg:sticky lg:top-7">
      <h2 className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-400">
        History
      </h2>
      {history.length === 0 ? (
        <p className="text-sm text-slate-400">
          Your questions from this session will appear here.
        </p>
      ) : (
        <ul className="flex flex-col gap-1.5">
          {history.map((entry) => {
            const active = entry.question === activeQuestion;
            return (
              <li key={entry.id}>
                <button
                  onClick={() => onRestore(entry)}
                  className={`w-full rounded-lg px-3 py-2 text-left text-sm transition ${
                    active
                      ? "bg-indigo-50 text-indigo-700"
                      : "text-slate-600 hover:bg-slate-50"
                  }`}
                >
                  <span className="line-clamp-2">{entry.question}</span>
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </aside>
  );
}
