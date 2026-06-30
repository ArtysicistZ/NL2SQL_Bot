"use client";

import { Fragment, type ReactNode } from "react";

import { SkeletonLines } from "@/components/Skeleton";

interface AnswerCardProps {
  answer: string;
  loading: boolean;
}

// Minimal inline formatting: **bold** segments, preserving line breaks.
function renderInline(text: string): ReactNode[] {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i} className="font-semibold text-slate-900">{part.slice(2, -2)}</strong>;
    }
    return <Fragment key={i}>{part}</Fragment>;
  });
}

export function AnswerCard({ answer, loading }: AnswerCardProps) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-400">
        Answer
      </h2>
      {loading ? (
        <SkeletonLines lines={4} />
      ) : answer ? (
        <div className="space-y-1 text-[15px] leading-relaxed text-slate-700">
          {answer.split("\n").map((line, i) => (
            <p key={i} className={line.trim() === "" ? "h-2" : undefined}>
              {renderInline(line)}
            </p>
          ))}
        </div>
      ) : (
        <p className="text-sm text-slate-400">
          Ask a question to see a natural-language answer here.
        </p>
      )}
    </section>
  );
}
