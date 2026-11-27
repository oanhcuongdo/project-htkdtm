import React, { useEffect, useState } from 'react';
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
import {
  BarChart3,
  Building2,
  Clock,
  ExternalLink,
  Layers,
  LayoutDashboard,
  RefreshCw,
  TrendingUp,
} from 'lucide-react';
import { fetchMarketBIOverview } from '../services/biService';
import { formatExactVND } from '../utils/formatters';

// Cấu hình URL nhúng Apache Superset Dashboard (ưu tiên biến môi trường .env hoặc mặc định localhost:8088)
const DEFAULT_SUPERSET_DASHBOARD_URL = 'http://localhost:8088/superset/dashboard/1/?standalone=true';
const SUPERSET_DASHBOARD_URL = (
  import.meta.env.VITE_SUPERSET_DASHBOARD_URL || DEFAULT_SUPERSET_DASHBOARD_URL
).trim();
const DEFAULT_SUPERSET_HOME = 'http://localhost:8088';

const PIE_COLORS = ['#0F766E', '#0369A1', '#D97706', '#7C3AED', '#E11D48', '#059669'];

export function AnalyticsPage() {
  const [activeTab, setActiveTab] = useState('live');

  const [biData, setBiData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const loadOverview = async () => {
    setIsLoading(true);
    setErrorMsg('');
    try {
      const data = await fetchMarketBIOverview();
      setBiData(data);
    } catch (err) {
      setErrorMsg(err?.response?.data?.detail || 'Không thể tải dữ liệu phân tích thị trường.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadOverview();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header + Tabs chuyển đổi */}
      <div className="flex flex-col gap-4 rounded-2xl border border-teal-100 bg-white p-6 shadow-xs lg:flex-row lg:items-center lg:justify-between">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#0F766E] text-white">
              <BarChart3 className="h-5 w-5" />
            </span>
            <div>
              <h1 className="text-xl font-bold text-[#134E4A]">
                Dashboard Phân Tích Thị Trường Nhà Thuê (BI)
              </h1>
              <p className="text-xs sm:text-sm text-[#475569]">
                Trực quan hóa Star Schema trên Supabase &amp; Apache Superset · Nhóm 12 (65HTTT)
              </p>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="flex rounded-xl bg-slate-100 p-1">
            <button
              type="button"
              onClick={() => setActiveTab('live')}
              className={`inline-flex items-center gap-1.5 rounded-lg px-3.5 py-2 text-xs sm:text-sm font-semibold transition-all ${
                activeTab === 'live'
                  ? 'bg-white text-[#0F766E] shadow-xs'
                  : 'text-[#475569] hover:text-[#134E4A]'
              }`}
            >
              <TrendingUp className="h-4 w-4" />
              BI Trực tiếp (3 Nhóm Insight)
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('superset')}
              className={`inline-flex items-center gap-1.5 rounded-lg px-3.5 py-2 text-xs sm:text-sm font-semibold transition-all ${
                activeTab === 'superset'
                  ? 'bg-white text-[#0F766E] shadow-xs'
                  : 'text-[#475569] hover:text-[#134E4A]'
              }`}
            >
              <LayoutDashboard className="h-4 w-4" />
              Apache Superset Embedded
            </button>
          </div>

          <a
            href={SUPERSET_DASHBOARD_URL || DEFAULT_SUPERSET_HOME}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 rounded-xl border border-teal-200 bg-teal-50/70 px-3.5 py-2 text-xs sm:text-sm font-semibold text-[#0F766E] hover:bg-teal-100 transition-colors"
            title="Mở giao diện quản trị Apache Superset"
          >
            <ExternalLink className="h-4 w-4" />
            Mở Superset
          </a>
        </div>
      </div>

      {/* TAB 1: LIVE BI INTERACTIVE (3 NHÓM INSIGHT) */}
      {activeTab === 'live' && (
        <div className="space-y-6">
          {errorMsg && (
            <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              {errorMsg}
            </div>
          )}

          {isLoading && !biData ? (
            <div className="rounded-2xl border border-teal-100 bg-white p-12 text-center text-sm text-[#475569]">
              <RefreshCw className="mx-auto h-6 w-6 animate-spin text-[#0F766E]" />
              <p className="mt-2">Đang tổng hợp chỉ số thị trường từ Star Schema...</p>
            </div>
          ) : biData ? (
            <>
              {/* KPI Summary Cards */}
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 sm:gap-4">
                <div className="rounded-2xl border border-teal-100 bg-white p-4 shadow-xs">
                  <div className="flex items-center justify-between text-xs text-[#475569]">
                    <span>Tổng nguồn cung active</span>
                    <Building2 className="h-4 w-4 text-[#0F766E]" />
                  </div>
                  <p className="mt-2 text-2xl font-bold text-[#134E4A]">
                    {biData.total_active_listings.toLocaleString('vi-VN')}
                  </p>
                  <p className="mt-0.5 text-[11px] text-slate-500">
                    Phủ sóng {biData.total_districts} quận/huyện
                  </p>
                </div>

                <div className="rounded-2xl border border-teal-100 bg-white p-4 shadow-xs">
                  <div className="flex items-center justify-between text-xs text-[#475569]">
                    <span>Giá thuê trung bình</span>
                    <TrendingUp className="h-4 w-4 text-[#0369A1]" />
                  </div>
                  <p className="mt-2 text-2xl font-bold text-[#0369A1]">
                    {formatExactVND(biData.avg_price)}
                  </p>
                  <p className="mt-0.5 text-[11px] text-slate-500">Toàn thị trường Hà Nội</p>
                </div>

                <div className="rounded-2xl border border-teal-100 bg-white p-4 shadow-xs">
                  <div className="flex items-center justify-between text-xs text-[#475569]">
                    <span>Đơn giá trung bình / m²</span>
                    <Layers className="h-4 w-4 text-[#0F766E]" />
                  </div>
                  <p className="mt-2 text-2xl font-bold text-[#0F766E]">
                    {formatExactVND(biData.avg_price_per_m2)}
                  </p>
                  <p className="mt-0.5 text-[11px] text-slate-500">Trên mỗi m² / tháng</p>
                </div>

                <div className="rounded-2xl border border-teal-100 bg-white p-4 shadow-xs">
                  <div className="flex items-center justify-between text-xs text-[#475569]">
                    <span>Thời gian lưu tin TB</span>
                    <Clock className="h-4 w-4 text-amber-600" />
                  </div>
                  <p className="mt-2 text-2xl font-bold text-amber-700">
                    {biData.avg_days_on_market !== null ? `${biData.avg_days_on_market} ngày` : '—'}
                  </p>
                  <p className="mt-0.5 text-[11px] text-slate-500">Chỉ số độ thanh khoản</p>
                </div>
              </div>

              {/* NHÓM INSIGHT 1: MẶT BẰNG GIÁ THUÊ / M² */}
              <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                <section className="rounded-2xl border border-teal-100 bg-white p-5 shadow-xs">
                  <div className="mb-4">
                    <span className="inline-block rounded-full bg-teal-50 px-2.5 py-0.5 text-[11px] font-semibold text-[#0F766E]">
                      Insight 1 · Mặt bằng giá thuê/m²
                    </span>
                    <h2 className="mt-1 text-base font-bold text-[#134E4A]">
                      Đơn giá thuê trung bình (VNĐ/m²) theo Quận/Huyện
                    </h2>
                  </div>
                  <div className="h-72 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={biData.price_by_district.slice(0, 10)}
                        margin={{ top: 5, right: 15, left: 0, bottom: 35 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                        <XAxis
                          dataKey="district"
                          tick={{ fontSize: 11 }}
                          angle={-25}
                          textAnchor="end"
                          interval={0}
                        />
                        <YAxis tick={{ fontSize: 11 }} />
                        <Tooltip formatter={(v) => [formatExactVND(v), 'Đơn giá/m²']} />
                        <Bar
                          dataKey="avg_price_per_m2"
                          name="Đơn giá TB (VNĐ/m²)"
                          fill="#0F766E"
                          radius={[6, 6, 0, 0]}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </section>

                <section className="rounded-2xl border border-teal-100 bg-white p-5 shadow-xs">
                  <div className="mb-4">
                    <span className="inline-block rounded-full bg-sky-50 px-2.5 py-0.5 text-[11px] font-semibold text-[#0369A1]">
                      Insight 1 · Theo loại hình
                    </span>
                    <h2 className="mt-1 text-base font-bold text-[#134E4A]">
                      Giá thuê trung bình theo Loại hình nhà ở
                    </h2>
                  </div>
                  <div className="h-72 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={biData.price_by_property_type}
                        margin={{ top: 5, right: 15, left: 10, bottom: 25 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                        <XAxis dataKey="type_name" tick={{ fontSize: 11 }} />
                        <YAxis tick={{ fontSize: 11 }} />
                        <Tooltip formatter={(v) => [formatExactVND(v), 'Giá thuê TB']} />
                        <Bar
                          dataKey="avg_price"
                          name="Giá thuê TB (VNĐ)"
                          fill="#0369A1"
                          radius={[6, 6, 0, 0]}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </section>
              </div>

              {/* NHÓM INSIGHT 2: NGUỒN CUNG THEO QUẬN & PHÂN KHÚC */}
              <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
                <section className="rounded-2xl border border-teal-100 bg-white p-5 shadow-xs lg:col-span-2">
                  <div className="mb-4">
                    <span className="inline-block rounded-full bg-teal-50 px-2.5 py-0.5 text-[11px] font-semibold text-[#0F766E]">
                      Insight 2 · Nguồn cung thị trường
                    </span>
                    <h2 className="mt-1 text-base font-bold text-[#134E4A]">
                      Phân bổ số lượng tin đăng theo Quận/Huyện
                    </h2>
                  </div>
                  <div className="h-72 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={biData.price_by_district.slice(0, 10)}
                        margin={{ top: 5, right: 15, left: -10, bottom: 35 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                        <XAxis
                          dataKey="district"
                          tick={{ fontSize: 11 }}
                          angle={-25}
                          textAnchor="end"
                          interval={0}
                        />
                        <YAxis tick={{ fontSize: 11 }} />
                        <Tooltip />
                        <Bar
                          dataKey="listing_count"
                          name="Số lượng tin đăng"
                          fill="#059669"
                          radius={[6, 6, 0, 0]}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </section>

                <section className="rounded-2xl border border-teal-100 bg-white p-5 shadow-xs">
                  <div className="mb-4">
                    <span className="inline-block rounded-full bg-amber-50 px-2.5 py-0.5 text-[11px] font-semibold text-amber-700">
                      Insight 2 · Phân khúc giá
                    </span>
                    <h2 className="mt-1 text-base font-bold text-[#134E4A]">
                      Cơ cấu phân khúc giá thuê
                    </h2>
                  </div>
                  <div className="h-72 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Tooltip />
                        <Legend wrapperStyle={{ fontSize: 12 }} />
                        <Pie
                          data={biData.supply_by_segment}
                          dataKey="listing_count"
                          nameKey="label"
                          cx="50%"
                          cy="45%"
                          innerRadius={40}
                          outerRadius={80}
                          paddingAngle={3}
                        >
                          {biData.supply_by_segment.map((_, idx) => (
                            <Cell key={idx} fill={PIE_COLORS[idx % PIE_COLORS.length]} />
                          ))}
                        </Pie>
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </section>
              </div>

              {/* NHÓM INSIGHT 3: BIẾN ĐỘNG GIÁ & ĐỘ THANH KHOẢN */}
              <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                <section className="rounded-2xl border border-teal-100 bg-white p-5 shadow-xs">
                  <div className="mb-4">
                    <span className="inline-block rounded-full bg-sky-50 px-2.5 py-0.5 text-[11px] font-semibold text-[#0369A1]">
                      Insight 3 · Biến động theo thời gian
                    </span>
                    <h2 className="mt-1 text-base font-bold text-[#134E4A]">
                      Xu hướng đơn giá/m² qua các tháng
                    </h2>
                  </div>
                  <div className="h-72 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart
                        data={biData.trend_by_month}
                        margin={{ top: 5, right: 15, left: 0, bottom: 15 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                        <XAxis dataKey="period" tick={{ fontSize: 11 }} />
                        <YAxis tick={{ fontSize: 11 }} />
                        <Tooltip formatter={(v) => [formatExactVND(v), 'Đơn giá TB/m²']} />
                        <Legend wrapperStyle={{ fontSize: 12 }} />
                        <Line
                          type="monotone"
                          dataKey="avg_price_per_m2"
                          name="Đơn giá TB (VNĐ/m²)"
                          stroke="#0369A1"
                          strokeWidth={2.5}
                          dot={{ r: 4 }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </section>

                <section className="rounded-2xl border border-teal-100 bg-white p-5 shadow-xs">
                  <div className="mb-4">
                    <span className="inline-block rounded-full bg-amber-50 px-2.5 py-0.5 text-[11px] font-semibold text-amber-700">
                      Insight 3 · Độ thanh khoản thị trường
                    </span>
                    <h2 className="mt-1 text-base font-bold text-[#134E4A]">
                      Số ngày lưu tin trung bình (Days on Market) theo Quận
                    </h2>
                  </div>
                  <div className="h-72 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={biData.liquidity_by_district}
                        margin={{ top: 5, right: 15, left: -10, bottom: 35 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                        <XAxis
                          dataKey="district"
                          tick={{ fontSize: 11 }}
                          angle={-25}
                          textAnchor="end"
                          interval={0}
                        />
                        <YAxis tick={{ fontSize: 11 }} />
                        <Tooltip formatter={(v) => [`${v} ngày`, 'Lưu tin TB']} />
                        <Bar
                          dataKey="avg_days_on_market"
                          name="Số ngày lưu tin TB"
                          fill="#D97706"
                          radius={[6, 6, 0, 0]}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </section>
              </div>
            </>
          ) : null}
        </div>
      )}

      {/* TAB 2: APACHE SUPERSET EMBEDDED */}
      {activeTab === 'superset' && (
        <div className="space-y-4">
          {SUPERSET_DASHBOARD_URL ? (
            <div className="overflow-hidden rounded-2xl border border-teal-200 bg-white shadow-sm">
              <iframe
                src={SUPERSET_DASHBOARD_URL}
                title="Apache Superset BI Dashboard"
                className="h-[78vh] w-full border-0"
                allowFullScreen
              />
            </div>
          ) : (
            <div className="rounded-2xl border border-dashed border-teal-300 bg-white p-8 shadow-xs">
              <div className="mx-auto max-w-2xl space-y-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-teal-50 text-[#0F766E]">
                    <LayoutDashboard className="h-6 w-6" />
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-[#134E4A]">
                      Chưa cấu hình URL Apache Superset Dashboard
                    </h2>
                    <p className="text-xs sm:text-sm text-[#475569]">
                      Thực hiện 4 bước bên dưới để bật Docker Superset, kết nối Supabase và nhúng Dashboard vào đây.
                    </p>
                  </div>
                </div>

                <ol className="list-decimal space-y-2 pl-5 text-xs sm:text-sm text-[#334155]">
                  <li>
                    Khởi chạy Docker Superset từ thư mục gốc dự án:{' '}
                    <code className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-xs text-[#0F766E]">
                      docker compose -f superset/docker-compose.superset.yml up -d
                    </code>
                  </li>
                  <li>
                    Truy cập{' '}
                    <a
                      href={DEFAULT_SUPERSET_HOME}
                      target="_blank"
                      rel="noreferrer"
                      className="font-semibold text-[#0369A1] underline"
                    >
                      http://localhost:8088
                    </a>{' '}
                    (tài khoản mặc định: <code>admin</code> / <code>admin123</code>).
                  </li>
                  <li>
                    Kết nối PostgreSQL tới Supabase (Session Pooler) và tạo Dataset từ view{' '}
                    <code className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-xs">
                      public.view_rental_market_analytics
                    </code>
                    .
                  </li>
                  <li>
                    Tạo Dashboard, nhấn <strong>Publish</strong>, rồi dán URL dạng{' '}
                    <code className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-xs">
                      http://localhost:8088/superset/dashboard/1/?standalone=true
                    </code>{' '}
                    vào ô phía trên hoặc biến <code>VITE_SUPERSET_DASHBOARD_URL</code>.
                  </li>
                </ol>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
