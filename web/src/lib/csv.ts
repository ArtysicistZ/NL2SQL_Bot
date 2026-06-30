// Serialize SQL results (positional rows) to CSV and trigger a download.

function escapeCell(value: unknown): string {
  if (value === null || value === undefined) return "";
  const str = String(value);
  if (/[",\n\r]/.test(str)) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

export function toCsv(columns: string[], rows: unknown[][]): string {
  const header = columns.map(escapeCell).join(",");
  const body = rows.map((row) => row.map(escapeCell).join(",")).join("\n");
  return body ? `${header}\n${body}` : header;
}

export function downloadCsv(
  columns: string[],
  rows: unknown[][],
  filename = "nl2sql-results.csv",
): void {
  const csv = toCsv(columns, rows);
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
