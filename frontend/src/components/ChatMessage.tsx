'use client';

import { useState } from 'react';
import { ChevronDown, ChevronRight, Database, AlertCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Message } from '@/types';
import { ChartRenderer } from './ChartRenderer';
import { ExportMenu } from './ExportMenu';
import { DataTable } from './DataTable';
import { clsx } from 'clsx';

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const [sqlExpanded, setSqlExpanded] = useState(false);
  const isUser = message.role === 'user';

  const hasChart = message.rawData && message.suggestedChartType && message.chartConfig;
  const hasTableData = message.rawData && message.rawData.length > 0;

  return (
    <div
      className={clsx(
        'animate-fade-in-up',
        isUser ? 'flex justify-end' : 'flex justify-start'
      )}
    >
      <div
        className={clsx(
          'max-w-[85%] rounded-2xl px-4 py-3',
          isUser
            ? 'bg-user-bubble dark:bg-user-bubble-dark text-gray-900 dark:text-gray-100'
            : 'bg-assistant-bubble dark:bg-assistant-bubble-dark',
          message.isError && 'border border-red-200 dark:border-red-800'
        )}
      >
        {/* Error icon */}
        {message.isError && (
          <div className="flex items-center gap-2 mb-2 text-red-500 dark:text-red-400">
            <AlertCircle className="w-4 h-4" />
            <span className="text-xs font-medium">Error</span>
          </div>
        )}

        {/* Message content */}
        <div className="prose prose-sm dark:prose-invert max-w-none break-words">
          {isUser ? (
            <p className="m-0 whitespace-pre-wrap">{message.content}</p>
          ) : (
            <ReactMarkdown>{message.content}</ReactMarkdown>
          )}
        </div>

        {/* Data Table — always shown when rawData exists */}
        {hasTableData && (
          <div className="mt-3">
            <DataTable data={message.rawData!} />
          </div>
        )}

        {/* Chart — only shown when chart analysis found a suitable visualization */}
        {hasChart && (
          <div className="mt-3">
            <ChartRenderer
              rawData={message.rawData!}
              suggestedChartType={message.suggestedChartType!}
              chartConfig={message.chartConfig!}
            />
          </div>
        )}

        {/* SQL Accordion */}
        {message.sql && (
          <div className="mt-3 border-t border-gray-200 dark:border-gray-700 pt-2">
            <button
              onClick={() => setSqlExpanded(!sqlExpanded)}
              className="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors"
              aria-expanded={sqlExpanded}
            >
              {sqlExpanded ? (
                <ChevronDown className="w-3.5 h-3.5" />
              ) : (
                <ChevronRight className="w-3.5 h-3.5" />
              )}
              <Database className="w-3.5 h-3.5" />
              <span>View SQL Query</span>
            </button>
            {sqlExpanded && (
              <pre className="mt-2 p-3 bg-gray-100 dark:bg-gray-800 rounded-lg text-xs overflow-x-auto">
                <code>{message.sql}</code>
              </pre>
            )}
          </div>
        )}

        {/* Export + metadata */}
        {!isUser && !message.isError && (
          <div className="mt-2 flex items-center justify-between">
            <div className="flex items-center gap-2">
              {message.domain && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400">
                  {message.domain}
                </span>
              )}
              {message.rowCount != null && message.rowCount > 0 && (
                <span className="text-xs text-gray-400 dark:text-gray-500">
                  {message.rowCount} row{message.rowCount !== 1 ? 's' : ''}
                </span>
              )}
            </div>
            <ExportMenu message={message} />
          </div>
        )}
      </div>
    </div>
  );
}
