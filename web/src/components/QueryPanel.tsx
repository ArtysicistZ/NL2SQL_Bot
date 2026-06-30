"use client";

interface QueryPanelProps {
  question: string;
  setQuestion: (value: string) => void;
  onAsk: (q?: string) => void;
  loading: boolean;
}

const EXAMPLES = [
  "What are the top 10 actors by number of films?",
  "How many films are there for each rating?",
  "Show the 5 longest films with their length.",
];

export function QueryPanel({ question, setQuestion, onAsk, loading }: QueryPanelProps) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <label htmlFor="question" className="mb-2 block text-sm font-medium text-slate-700">
        Ask a question about the database
      </label>
      <textarea
        id="question"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
            e.preventDefault();
            onAsk();
          }
        }}
        placeholder="e.g. What are the top 10 actors by number of films?"
        rows={3}
        className="max-h-40 w-full resize-y rounded-lg border border-slate-300 p-3 text-[15px] text-slate-800 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
      />
      <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap gap-2">
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              onClick={() => {
                setQuestion(ex);
                onAsk(ex);
              }}
              disabled={loading}
              className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-600 transition hover:border-indigo-200 hover:bg-indigo-50 hover:text-indigo-700 disabled:opacity-50"
            >
              {ex}
            </button>
          ))}
        </div>
        <button
          onClick={() => onAsk()}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-5 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading && (
            <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
            </svg>
          )}
          {loading ? "Thinking…" : "Ask"}
        </button>
      </div>
      <p className="mt-2 text-xs text-slate-400">Press ⌘/Ctrl + Enter to submit.</p>
    </section>
  );
}
