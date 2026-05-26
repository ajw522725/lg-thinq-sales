import type { ReactNode } from "react";

interface DataTableProps {
  headers: string[];
  rows: ReactNode[][];
}

export function DataTable({ headers, rows }: DataTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left">
        <thead>
          <tr className="border-b border-surface-high text-xs font-bold uppercase tracking-wide text-secondary">
            {headers.map((header) => (
              <th key={header} className="px-4 py-4">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-surface-high">
          {rows.map((row, index) => (
            <tr key={index} className="hover:bg-primary/[0.02]">
              {row.map((cell, cellIndex) => (
                <td key={cellIndex} className="px-4 py-5 align-top text-sm">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
