"use client";

interface ErrorBannerProps {
  message: string;
  onRetry?: () => void;
  onDismiss?: () => void;
}

export function ErrorBanner({ message, onRetry, onDismiss }: ErrorBannerProps) {
  return (
    <div
      role="alert"
      className="flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
    >
      <svg className="mt-0.5 h-5 w-5 shrink-0 text-red-500" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
        <path fillRule="evenodd" d="M18 10A8 8 0 11.001 10 8 8 0 0118 10zM9 5a1 1 0 012 0v5a1 1 0 11-2 0V5zm1 9a1.25 1.25 0 100-2.5 1.25 1.25 0 000 2.5z" clipRule="evenodd" />
      </svg>
      <p className="flex-1 leading-relaxed">{message}</p>
      <div className="flex shrink-0 items-center gap-2">
        {onRetry && (
          <button
            onClick={onRetry}
            className="rounded-md bg-red-100 px-2.5 py-1 text-xs font-medium text-red-800 transition hover:bg-red-200"
          >
            Retry
          </button>
        )}
        {onDismiss && (
          <button
            onClick={onDismiss}
            aria-label="Dismiss error"
            className="rounded-md px-1.5 py-1 text-red-500 transition hover:bg-red-100"
          >
            ✕
          </button>
        )}
      </div>
    </div>
  );
}
