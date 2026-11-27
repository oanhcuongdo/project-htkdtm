import type { ReactNode } from 'react';

/*
 * Chart accessibility helpers — UI_SPEC §8/§10: every chart needs a legend
 * (colour alone is never the only signal) and a text/table alternative for
 * screen readers.
 */

export function ChartLegend({
  items,
}: {
  items: { label: string; color: string }[];
}) {
  return (
    <ul className="mb-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted">
      {items.map((item) => (
        <li key={item.label} className="flex items-center gap-1.5">
          <span
            className="size-2 shrink-0 rounded-full"
            style={{ backgroundColor: item.color }}
            aria-hidden="true"
          />
          {item.label}
        </li>
      ))}
    </ul>
  );
}

/** Visually hidden data table that mirrors the chart. */
export function ChartTable({
  caption,
  head,
  rows,
}: {
  caption: string;
  head: string[];
  rows: (string | number)[][];
}) {
  return (
    <table className="sr-only">
      <caption>{caption}</caption>
      <thead>
        <tr>
          {head.map((cell) => (
            <th key={cell} scope="col">
              {cell}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, rowIndex) => (
          <tr key={rowIndex}>
            {row.map((cell, cellIndex) => (
              <td key={cellIndex}>{cell}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

/** Chart surface with an accessible name and an optional sr-only table. */
export function ChartSurface({
  label,
  height = 256,
  children,
  table,
}: {
  label: string;
  height?: number;
  children: ReactNode;
  table?: ReactNode;
}) {
  return (
    <>
      <div className="w-full" style={{ height }} role="img" aria-label={label}>
        {children}
      </div>
      {table}
    </>
  );
}
