'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

interface DataTableProps {
  data: Record<string, unknown>[];
}

const INITIAL_ROWS = 20;

function formatHeader(key: string): string {
  return key
    .replace(/_id$/i, ' ID')
    .replace(/_lpa$/i, ' (LPA)')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatValue(val: unknown): string {
  if (val === null || val === undefined) return '-';
  if (typeof val === 'number') {
    if (Number.isInteger(val)) return val.toString();
    return val.toFixed(2);
  }
  return String(val);
}

export function DataTable({ data }: DataTableProps) {
  const [expanded, setExpanded] = useState(false);

  if (!data || data.length === 0) return null;

  const headers = Object.keys(data[0]);
  const showToggle = data.length > INITIAL_ROWS;
  const displayData = expanded ? data : data.slice(0, INITIAL_ROWS);

  return (
    <div className="border border-border-light dark:border-border-dark rounded-xl overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-gray-50 dark:bg-gray-800/50">
              {headers.map((key) => (
                <th
                  key={key}
                  className="px-3 py-2.5 text-left font-semibold text-gray-600 dark:text-gray-300 whitespace-nowrap border-b border-border-light dark:border-border-dark"
                >
                  {formatHeader(key)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {displayData.map((row, idx) => (
              <tr
                key={idx}
                className={
                  idx % 2 === 0
                    ? 'bg-white dark:bg-gray-900/20'
                    : 'bg-gray-50/50 dark:bg-gray-800/20'
                }
              >
                {headers.map((key) => (
                  <td
                    key={key}
                    className="px-3 py-2 text-gray-700 dark:text-gray-300 whitespace-nowrap border-b border-border-light/50 dark:border-border-dark/50"
                  >
                    {formatValue(row[key])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Show more / less toggle */}
      {showToggle && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full flex items-center justify-center gap-1.5 py-2 text-xs text-blue-600 dark:text-blue-400 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors border-t border-border-light dark:border-border-dark"
        >
          {expanded ? (
            <>
              <ChevronUp className="w-3.5 h-3.5" />
              Show less
            </>
          ) : (
            <>
              <ChevronDown className="w-3.5 h-3.5" />
              Show all {data.length} rows
            </>
          )}
        </button>
      )}
    </div>
  );
}
