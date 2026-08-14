'use client';

import { useState } from 'react';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, Legend,
} from 'recharts';
import { useTheme } from 'next-themes';
import { ChartConfig } from '@/types';
import { BarChart3, LineChart as LineChartIcon, PieChart as PieChartIcon, AreaChart as AreaChartIcon } from 'lucide-react';

const CHART_COLORS = [
  '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
  '#06b6d4', '#ec4899', '#84cc16', '#f97316', '#6366f1',
];

interface ChartRendererProps {
  rawData: Record<string, unknown>[];
  suggestedChartType: string;
  chartConfig: ChartConfig;
}

type ChartType = 'bar' | 'line' | 'pie' | 'area';

const CHART_OPTIONS: { type: ChartType; icon: typeof BarChart3; label: string }[] = [
  { type: 'bar', icon: BarChart3, label: 'Bar' },
  { type: 'line', icon: LineChartIcon, label: 'Line' },
  { type: 'pie', icon: PieChartIcon, label: 'Pie' },
  { type: 'area', icon: AreaChartIcon, label: 'Area' },
];

export function ChartRenderer({ rawData, suggestedChartType, chartConfig }: ChartRendererProps) {
  const [chartType, setChartType] = useState<ChartType>(suggestedChartType as ChartType || 'bar');
  const { theme } = useTheme();

  const isDark = theme === 'dark';
  const textColor = isDark ? '#9ca3af' : '#6b7280';
  const gridColor = isDark ? '#374151' : '#e5e7eb';

  const { x_key, y_keys, title } = chartConfig;

  if (!rawData || rawData.length === 0) return null;

  // Build cleaned chart data (only x_key + y_keys, with numeric conversion)
  const chartData = rawData.map((row) => {
    const cleaned: Record<string, unknown> = { [x_key]: row[x_key] };
    for (const col of y_keys) {
      const val = row[col];
      if (val !== null && val !== undefined) {
        try {
          cleaned[col] = typeof val === 'number' ? val : Number(val);
        } catch {
          cleaned[col] = 0;
        }
      } else {
        cleaned[col] = 0;
      }
    }
    return cleaned;
  });

  const renderChart = () => {
    switch (chartType) {
      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
              <XAxis dataKey={x_key} tick={{ fill: textColor, fontSize: 12 }} />
              <YAxis tick={{ fill: textColor, fontSize: 12 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: isDark ? '#1f2937' : '#ffffff',
                  border: `1px solid ${gridColor}`,
                  borderRadius: '8px',
                  color: isDark ? '#f3f4f6' : '#111827',
                }}
              />
              <Legend />
              {y_keys.map((key, idx) => (
                <Bar key={key} dataKey={key} fill={CHART_COLORS[idx % CHART_COLORS.length]} radius={[4, 4, 0, 0]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        );
      case 'line':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
              <XAxis dataKey={x_key} tick={{ fill: textColor, fontSize: 12 }} />
              <YAxis tick={{ fill: textColor, fontSize: 12 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: isDark ? '#1f2937' : '#ffffff',
                  border: `1px solid ${gridColor}`,
                  borderRadius: '8px',
                  color: isDark ? '#f3f4f6' : '#111827',
                }}
              />
              <Legend />
              {y_keys.map((key, idx) => (
                <Line key={key} type="monotone" dataKey={key} stroke={CHART_COLORS[idx % CHART_COLORS.length]} strokeWidth={2} dot={{ r: 4 }} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        );
      case 'pie':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={chartData}
                dataKey={y_keys[0]}
                nameKey={x_key}
                cx="50%"
                cy="50%"
                outerRadius={100}
                label={({ name, value }) => `${name}: ${value}`}
              >
                {chartData.map((_, idx) => (
                  <Cell key={`cell-${idx}`} fill={CHART_COLORS[idx % CHART_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: isDark ? '#1f2937' : '#ffffff',
                  border: `1px solid ${gridColor}`,
                  borderRadius: '8px',
                  color: isDark ? '#f3f4f6' : '#111827',
                }}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        );
      case 'area':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
              <XAxis dataKey={x_key} tick={{ fill: textColor, fontSize: 12 }} />
              <YAxis tick={{ fill: textColor, fontSize: 12 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: isDark ? '#1f2937' : '#ffffff',
                  border: `1px solid ${gridColor}`,
                  borderRadius: '8px',
                  color: isDark ? '#f3f4f6' : '#111827',
                }}
              />
              <Legend />
              {y_keys.map((key, idx) => (
                <Area key={key} type="monotone" dataKey={key} fill={CHART_COLORS[idx % CHART_COLORS.length]} stroke={CHART_COLORS[idx % CHART_COLORS.length]} fillOpacity={0.3} />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        );
      default:
        return null;
    }
  };

  return (
    <div className="border border-border-light dark:border-border-dark rounded-xl p-4">
      {/* Chart controls */}
      <div className="flex items-center justify-between mb-3">
        {title && (
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">{title}</h4>
        )}
        <div className="flex items-center gap-1">
          {CHART_OPTIONS.map(({ type, icon: Icon, label }) => (
            <button
              key={type}
              onClick={() => setChartType(type)}
              className={`p-1.5 rounded-md transition-colors ${
                chartType === type
                  ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                  : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'
              }`}
              aria-label={`Show ${label} chart`}
              title={label}
            >
              <Icon className="w-4 h-4" />
            </button>
          ))}
        </div>
      </div>

      {renderChart()}
    </div>
  );
}
