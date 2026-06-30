"use client";

import { AnswerCard } from "@/components/AnswerCard";
import { ChartView } from "@/components/ChartView";
import { ErrorBanner } from "@/components/ErrorBanner";
import { HistoryPanel } from "@/components/HistoryPanel";
import { QueryPanel } from "@/components/QueryPanel";
import { ResultsTable } from "@/components/ResultsTable";
import { SqlEditor } from "@/components/SqlEditor";
import { useNl2Sql } from "@/hooks/useNl2Sql";

const STACK = ["Google ADK", "OpenAI", "FastAPI", "Next.js", "MySQL"];

const cardTitle = "mb-3 text-xs font-semibold uppercase tracking-wide text-slate-400";

export default function Home() {
  const nl = useNl2Sql();
  const busy = nl.phase === "asking" || nl.phase === "running";
  const showResults = nl.current !== null;
  const isTableConfig = nl.current?.plotConfig?.type === "table";

  return (
    <div className="mx-auto max-w-7xl px-4 py-7 sm:px-6">
      <header className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-600 text-lg font-bold text-white">
            ⌘
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">NL2SQL</h1>
            <p className="text-sm text-slate-500">
              Ask your database in plain English — answer, chart, and SQL.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {STACK.map((s) => (
            <span
              key={s}
              className="rounded-full bg-white px-2.5 py-0.5 text-xs font-medium text-slate-500 ring-1 ring-slate-200"
            >
              {s}
            </span>
          ))}
        </div>
      </header>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-[minmax(0,1fr)_260px]">
        <main className="flex flex-col gap-5">
          <QueryPanel
            question={nl.question}
            setQuestion={nl.setQuestion}
            onAsk={nl.ask}
            loading={busy}
          />

          {nl.phase === "error" && nl.error && (
            <ErrorBanner message={nl.error} onRetry={() => nl.ask()} onDismiss={nl.dismissError} />
          )}

          {busy && !showResults && (
            <AnswerCard answer="" loading={true} />
          )}

          {showResults && (
            <div className="grid grid-cols-1 items-start gap-5 xl:grid-cols-12">
              {/* Left column: answer + results table */}
              <div className="flex flex-col gap-5 xl:col-span-5">
                <AnswerCard answer={nl.current!.answer} loading={false} />
                <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                  <h2 className={cardTitle}>Results</h2>
                  <ResultsTable
                    result={nl.current!.result}
                    columnConfig={isTableConfig ? nl.current!.plotConfig.columns : undefined}
                  />
                </section>
              </div>

              {/* Right column: chart + SQL editor */}
              <div className="flex flex-col gap-5 xl:col-span-7">
                <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                  <h2 className={cardTitle}>{isTableConfig ? "Result" : "Chart"}</h2>
                  <ChartView plotConfig={nl.current!.plotConfig} result={nl.current!.result} />
                </section>
                <section className="rounded-xl border border-slate-800 bg-slate-950 p-5 shadow-sm">
                  <SqlEditor
                    editedSql={nl.editedSql}
                    setEditedSql={nl.setEditedSql}
                    onRerun={nl.rerunSql}
                    rerunning={nl.rerunning}
                    rerunError={nl.rerunError}
                  />
                </section>
              </div>
            </div>
          )}
        </main>

        <HistoryPanel
          history={nl.history}
          onRestore={nl.restore}
          activeQuestion={nl.current?.question}
        />
      </div>

      <footer className="mt-10 border-t border-slate-200 pt-6 text-center text-xs text-slate-400">
        Read-only SQL · allowlisted tables · powered by a Google ADK multi-agent pipeline.
      </footer>
    </div>
  );
}
