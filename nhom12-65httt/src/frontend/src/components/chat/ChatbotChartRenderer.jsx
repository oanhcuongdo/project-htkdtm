import React, { useState } from 'react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { BarChart3, Table as TableIcon } from 'lucide-react';
import { formatExactVND } from '../../utils/formatters';

const CHART_COLORS = [
  '#0F766E', // teal-700
  '#0369A1', // sky-700
  '#D97706', // amber-600
  '#7C3AED', // violet-600
  '#E11D48', // rose-600
  '#059669', // emerald-600
  '#EA580C', // orange-600
  '#4F46E5', // indigo-600
];

function formatValue(key, val) {
  if (val === null || val === undefined) return '—';
  if (typeof val === 'number') {
    if (key.includes('price') || key.includes('cost')) {
      return formatExactVND(val);
    }
    return val.toLocaleString('vi-VN');
  }
  return String(val);
}

function detectKeys(columns, rows) {
  if (!rows || rows.length === 0) return { labelKey: '', valueKeys: [] };

  const first = rows[0];
  let labelKey = columns.find((c) => typeof first[c] === 'string') || columns[0];
  const valueKeys = columns.filter((c) => c !== labelKey && typeof first[c] === 'number');

  return { labelKey, valueKeys: valueKeys.length > 0 ? valueKeys : columns.slice(1) };
}

export function ChatbotChartRenderer({ chartType = 'table', columns = [], rows = [] }) {
  const [viewMode, setViewMode] = useState(chartType === 'table' ? 'table' : 'chart');

  if (!rows || rows.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-teal-200 bg-teal-50/50 p-4 text-center text-xs text-[#475569]">
        Không có dữ liệu trả về cho biểu đồ.
      </div>
    );
  }

  const { labelKey, valueKeys } = detectKeys(columns, rows);

  return (
    <div className="mt-2.5 overflow-hidden rounded-xl border border-teal-100 bg-white shadow-xs">
      {/* Switcher giữa biểu đồ và bảng */}
      <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50/80 px-3 py-1.5 text-xs text-[#475569]">
        <span className="font-medium">
          Dữ liệu ({rows.length} kết quả)
        </span>
        <button
          type="button"
          onClick={() => setViewMode((m) => (m === 'chart' ? 'table' : 'chart'))}
          className="inline-flex items-center gap-1 rounded-md px-2 py-0.5 font-medium text-[#0F766E] hover:bg-teal-100/60 transition-colors"
        >
          {viewMode === 'chart' ? (
            <>
              <TableIcon className="h-3.5 w-3.5" /> Xem bảng
            </>
          ) : (
            <>
              <BarChart3 className="h-3.5 w-3.5" /> Xem biểu đồ
            </>
          )}
        </button>
      </div>

      <div className="p-2 sm:p-3">
        {viewMode === 'table' || !valueKeys.length ? (
          <div className="max-h-60 overflow-x-auto overflow-y-auto text-xs">
            <table className="w-full border-collapse text-left">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50 text-[#134E4A]">
                  {columns.map((col) => (
                    <th key={col} className="px-2.5 py-1.5 font-semibold whitespace-nowrap">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {rows.map((row, idx) => (
                  <tr key={idx} className="hover:bg-teal-50/40">
                    {columns.map((col) => (
                      <td key={col} className="px-2.5 py-1.5 whitespace-nowrap text-[#334155]">
                        {formatValue(col, row[col])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="h-60 w-full pt-1">
            <ResponsiveContainer width="100%" height="100%">
              {chartType === 'line' ? (
                <LineChart data={rows} margin={{ top: 10, right: 10, left: -15, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis
                    dataKey={labelKey}
                    tick={{ fontSize: 11 }}
                    angle={-25}
                    textAnchor="end"
                    interval={0}
                  />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip
                    formatter={(val, name) => [formatValue(name, val), name]}
                    contentStyle={{ borderRadius: 8, fontSize: 12 }}
                  />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  {valueKeys.map((vk, i) => (
                    <Line
                      key={vk}
                      type="monotone"
                      dataKey={vk}
                      stroke={CHART_COLORS[i % CHART_COLORS.length]}
                      strokeWidth={2}
                      dot={{ r: 3 }}
                    />
                  ))}
                </LineChart>
              ) : chartType === 'pie' ? (
                <PieChart>
                  <Tooltip
                    formatter={(val, name) => [formatValue(name, val), name]}
                    contentStyle={{ borderRadius: 8, fontSize: 12 }}
                  />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Pie
                    data={rows}
                    dataKey={valueKeys[0]}
                    nameKey={labelKey}
                    cx="50%"
                    cy="50%"
                    outerRadius={75}
                    innerRadius={30}
                    paddingAngle={2}
                  >
                    {rows.map((_, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={CHART_COLORS[index % CHART_COLORS.length]}
                      />
                    ))}
                  </Pie>
                </PieChart>
              ) : (
                /* Mặc định là bar chart */
                <BarChart data={rows} margin={{ top: 10, right: 10, left: -15, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis
                    dataKey={labelKey}
                    tick={{ fontSize: 11 }}
                    angle={-25}
                    textAnchor="end"
                    interval={0}
                  />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip
                    formatter={(val, name) => [formatValue(name, val), name]}
                    contentStyle={{ borderRadius: 8, fontSize: 12 }}
                  />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  {valueKeys.map((vk, i) => (
                    <Bar
                      key={vk}
                      dataKey={vk}
                      fill={CHART_COLORS[i % CHART_COLORS.length]}
                      radius={[4, 4, 0, 0]}
                    />
                  ))}
                </BarChart>
              )}
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}
