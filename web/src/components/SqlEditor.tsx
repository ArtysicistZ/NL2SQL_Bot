"use client";

import hljs from "highlight.js/lib/core";
import sql from "highlight.js/lib/languages/sql";
import { useEffect, useMemo, useState } from "react";

import { ErrorBanner } from "@/components/ErrorBanner";

hljs.registerLanguage("sql", sql);

interface SqlEditorProps {
  editedSql: string;
  setEditedSql: (value: string) => void;
  onRerun: () => void;
  rerunning: boolean;
  rerunError: string | null;
}

export function SqlEditor({
  editedSql,
  setEditedSql,
  onRerun,
  rerunning,
  rerunError,
}: SqlEditorProps) {
  const [editing, setEditing] = useState(false);
  const [copied, setCopied] = useState(false);

  const highlighted = useMemo(() => {
    if (!editedSql) return "";
    try {
      return hljs.highlight(editedSql, { language: "sql" }).value;
    } catch {
      return editedSql;
    }
  }, [editedSql]);

  useEffect(() => {
    if (!copied) return;
    const t = setTimeout(() => setCopied(false), 2000);
    return () => clearTimeout(t);
  }, [copied]);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(editedSql);
      setCopied(true);
    } catch {
      /* clipboard unavailable */
    }
  };

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
          Generated SQL
        </h3>
        <div className="flex items-center gap-2">
          <button
            onClick={copy}
            className="rounded-md border border-slate-700 px-2.5 py-1 text-xs font-medium text-slate-300 transition hover:bg-slate-800"
          >
            {copied ? "Copied" : "Copy"}
          </button>
          <button
            onClick={() => setEditing((e) => !e)}
            className="rounded-md border border-slate-700 px-2.5 py-1 text-xs font-medium text-slate-300 transition hover:bg-slate-800"
          >
            {editing ? "Done" : "Edit"}
          </button>
        </div>
      </div>

      {editing ? (
        <textarea
          value={editedSql}
          onChange={(e) => setEditedSql(e.target.value)}
          spellCheck={false}
          rows={Math.min(14, Math.max(4, editedSql.split("\n").length + 1))}
          className="w-full resize-y rounded-lg border border-slate-700 bg-slate-900 p-3 font-mono text-sm text-slate-100 outline-none focus:border-indigo-500"
        />
      ) : (
        <pre className="max-h-[320px] overflow-auto rounded-lg bg-slate-900 p-3 text-sm">
          <code
            className="hljs language-sql !bg-transparent !p-0 font-mono"
            dangerouslySetInnerHTML={{ __html: highlighted }}
          />
        </pre>
      )}

      <div className="flex items-center gap-3">
        <button
          onClick={onRerun}
          disabled={rerunning || !editedSql.trim()}
          className="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {rerunning ? "Running…" : "Run SQL"}
        </button>
        <span className="text-xs text-slate-400">
          Edit the query and re-run it without asking the model again.
        </span>
      </div>

      {rerunError && <ErrorBanner message={rerunError} />}
    </div>
  );
}
