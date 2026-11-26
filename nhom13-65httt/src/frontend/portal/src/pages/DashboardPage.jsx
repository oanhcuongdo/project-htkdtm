import React, { useEffect, useState } from 'react'
import { AlertTriangle, ArrowDownRight, ArrowUpRight, ExternalLink, PiggyBank, RefreshCw, TrendingUp } from 'lucide-react'
import api from '../api/client'
import BrokenLine from '../components/brand/BrokenLine'

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
      ? 'bg-estonia-haapsalu border-[#E5CFA0] text-boulder-mustkivi'
      : 'bg-emerald-50 border-emerald-200 text-emerald-900'

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="text-left">
          <p className="text-xs font-semibold uppercase tracking-widest text-estonia-blue mb-1">
            Tổng quan tài chính cá nhân
          </p>
          <h2 className="font-display font-bold text-2xl sm:text-3xl tracking-tight text-boulder-mustkivi">
            Dòng tiền & BI Dashboard
          </h2>
          <div className="mt-2 mb-2">
            <BrokenLine color="#0030DE" className="w-32 h-2.5" strokeWidth={2.5} />
          </div>
          <p className="text-xs text-boulder-kabelikivi">
            Kỳ phân tích gần nhất: <span className="font-mono font-semibold text-boulder-mustkivi">{kpi?.target_period || '—'}</span>
          </p>
        </div>
        <button
          onClick={fetchKpi}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-full bg-boulder-ehakivi border border-boulder-hellamaa hover:border-estonia-blue hover:text-estonia-blue text-xs font-semibold text-boulder-mustkivi transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Làm mới số liệu
        </button>
      </div>

      {/* 4 KPI Limestone Cards cô lập theo user_id */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-boulder-ehakivi p-5 rounded-limestone border border-boulder-hellamaa">
          <div className="flex items-center justify-between text-xs font-semibold text-boulder-kabelikivi mb-2.5">
            <span>THU NHẬP THÁNG</span>
            <ArrowUpRight className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="font-display text-2xl font-bold text-boulder-mustkivi tabular-nums-vnd">
            {formatVnd(q4.mtd_income)}
          </div>
          <p className="text-xs text-boulder-kabelikivi mt-1.5">Đã loại trừ chuyển tiền nội bộ</p>
        </div>

        <div className="bg-boulder-ehakivi p-5 rounded-limestone border border-boulder-hellamaa">
          <div className="flex items-center justify-between text-xs font-semibold text-boulder-kabelikivi mb-2.5">
            <span>CHI TIÊU LŨY KẾ</span>
            <ArrowDownRight className="w-4 h-4 text-rose-600" />
          </div>
          <div className="font-display text-2xl font-bold text-boulder-mustkivi tabular-nums-vnd">
            {formatVnd(q4.mtd_expense)}
          </div>
          <p className="text-xs text-boulder-kabelikivi mt-1.5 tabular-nums-vnd">
            Burn-rate: {formatVnd(q4.daily_burn_rate)}/ngày
          </p>
        </div>

        <div className="bg-boulder-ehakivi p-5 rounded-limestone border border-boulder-hellamaa">
          <div className="flex items-center justify-between text-xs font-semibold text-boulder-kabelikivi mb-2.5">
            <span>TIẾT KIỆM RÒNG DỰ KIẾN</span>
            <PiggyBank className="w-4 h-4 text-estonia-blue" />
          </div>
          <div className="font-display text-2xl font-bold text-estonia-blue tabular-nums-vnd">
            {q4.projected_savings_rate_pct !== undefined ? `${q4.projected_savings_rate_pct}%` : '0%'}
          </div>
          <p className="text-xs text-boulder-kabelikivi mt-1.5 tabular-nums-vnd">
            Dùng {q4.budget_utilization_pct || 0}% hạn mức ngân sách
          </p>
        </div>

        <div className="bg-boulder-ehakivi p-5 rounded-limestone border border-boulder-hellamaa">
          <div className="flex items-center justify-between text-xs font-semibold text-boulder-kabelikivi mb-2.5">
            <span>SỐ DƯ CUỐI THÁNG DỰ KIẾN</span>
            <TrendingUp className="w-4 h-4 text-estonia-paldiski" />
          </div>
          <div className="font-display text-2xl font-bold text-boulder-mustkivi tabular-nums-vnd">
            {formatVnd(q4.projected_eom_balance)}
          </div>
          <p className="text-xs text-boulder-kabelikivi mt-1.5">
            {kpi?.q5_recent_anomalies?.length || 0} giao dịch bất thường AI đánh dấu
          </p>
        </div>
      </div>

      {/* Khuyến nghị thông minh */}
      {q4.advice && (
        <div className={`px-4 py-3.5 rounded-limestone border text-sm flex items-start gap-3 ${alertColor}`}>
          <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>{q4.advice}</span>
        </div>
      )}

      {/* Nhúng 3 Dashboard Apache Superset */}
      <div className="bg-boulder-ehakivi rounded-limestone border border-boulder-hellamaa overflow-hidden">
        <div className="px-4 py-3.5 border-b border-boulder-hellamaa flex flex-wrap items-center justify-between gap-3 bg-boulder-pahkla">
          <div className="flex flex-wrap gap-2">
            {SUPERSET_TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-2 rounded-full text-xs font-semibold transition-colors ${
                  activeTab === tab.id
                    ? 'bg-estonia-blue text-white'
                    : 'bg-boulder-ehakivi text-boulder-majakivi border border-boulder-hellamaa hover:border-estonia-blue hover:text-estonia-blue'
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
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-estonia-blue hover:text-estonia-paldiski transition-colors"
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
