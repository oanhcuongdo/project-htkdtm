import React, { useEffect, useState } from 'react'
import { AlertTriangle, ArrowDownRight, ArrowUpRight, ExternalLink, PiggyBank, RefreshCw, TrendingUp } from 'lucide-react'
import api from '../api/client'

const SUPERSET_BASE = 'http://localhost:8088'
const SUPERSET_TABS = [
  { id: 'cashflow-overview', label: '01. Tổng quan Dòng tiền (Cashflow)' },
  { id: 'spending-behavior', label: '02. Hành vi Chi tiêu (Heatmap & Donut)' },
  { id: 'ai-forecast-anomalies', label: '03. Dự báo 30 ngày & Bất thường AI' },
]

function formatVnd(val) {
  if (val === null || val === undefined) return '0 đ'
  return Number(val).toLocaleString('vi-VN') + ' đ'
}

export default function DashboardPage() {
  const [kpi, setKpi] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('cashflow-overview')

  const fetchKpi = async () => {
    setLoading(true)
    try {
      const res = await api.get('/analytics/kpi-summary')
      setKpi(res.data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchKpi()
  }, [])

  const q4 = kpi?.q4_projected_end_of_month_balance || {}
  const alertColor =
    q4.alert_level === 'DANGER'
      ? 'bg-rose-50 border-rose-200 text-rose-800'
      : q4.alert_level === 'WARNING'
      ? 'bg-amber-50 border-amber-200 text-amber-800'
      : 'bg-emerald-50 border-emerald-200 text-emerald-800'

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Tổng quan Dòng tiền & BI Dashboard</h2>
          <p className="text-sm text-slate-500">
            Kỳ phân tích gần nhất: <span className="font-semibold text-slate-700">{kpi?.target_period || '—'}</span>
          </p>
        </div>
        <button
          onClick={fetchKpi}
          className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-white border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-50 shadow-sm"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Làm mới số liệu
        </button>
      </div>

      {/* 4 KPI Cards cô lập theo user_id */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-500 mb-2">
            <span>THU NHẬP THÁNG</span>
            <ArrowUpRight className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="text-xl font-bold text-slate-900">{formatVnd(q4.mtd_income)}</div>
          <p className="text-xs text-slate-400 mt-1">Đã loại trừ chuyển tiền nội bộ</p>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-500 mb-2">
            <span>CHI TIÊU LŨY KẾ</span>
            <ArrowDownRight className="w-4 h-4 text-rose-500" />
          </div>
          <div className="text-xl font-bold text-slate-900">{formatVnd(q4.mtd_expense)}</div>
          <p className="text-xs text-slate-400 mt-1">Burn-rate: {formatVnd(q4.daily_burn_rate)}/ngày</p>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-500 mb-2">
            <span>TIẾT KIỆM RÒNG DỰ KIẾN</span>
            <PiggyBank className="w-4 h-4 text-indigo-500" />
          </div>
          <div className="text-xl font-bold text-indigo-700">
            {q4.projected_savings_rate_pct !== undefined ? `${q4.projected_savings_rate_pct}%` : '0%'}
          </div>
          <p className="text-xs text-slate-400 mt-1">Dùng {q4.budget_utilization_pct || 0}% hạn mức ngân sách</p>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-500 mb-2">
            <span>SỐ DƯ CUỐI THÁNG DỰ KIẾN</span>
            <TrendingUp className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-xl font-bold text-slate-900">{formatVnd(q4.projected_eom_balance)}</div>
          <p className="text-xs text-slate-400 mt-1">
            {kpi?.q5_recent_anomalies?.length || 0} giao dịch bất thường AI đánh dấu
          </p>
        </div>
      </div>

      {/* Khuyến nghị thông minh */}
      {q4.advice && (
        <div className={`px-4 py-3 rounded-xl border text-sm flex items-start gap-3 ${alertColor}`}>
          <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>{q4.advice}</span>
        </div>
      )}

      {/* Nhúng 3 Dashboard Apache Superset */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3 bg-slate-50">
          <div className="flex flex-wrap gap-2">
            {SUPERSET_TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-3.5 py-2 rounded-xl text-xs font-semibold transition ${
                  activeTab === tab.id
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-100'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <a
            href={`${SUPERSET_BASE}/superset/dashboard/${activeTab}/`}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-600 hover:text-indigo-800"
          >
            Mở trực tiếp trên Superset
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>

        <iframe
          key={activeTab}
          title={activeTab}
          src={`${SUPERSET_BASE}/superset/dashboard/${activeTab}/?standalone=true`}
          className="w-full h-[760px] border-0"
        />
      </div>
    </div>
  )
}
