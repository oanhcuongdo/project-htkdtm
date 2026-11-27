import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  ExternalLink,
  Eye,
  EyeOff,
  Filter,
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
  XCircle,
  FileSpreadsheet,
  Building,
} from 'lucide-react';
import { useSession } from '../contexts/SessionContext';
import { fetchAdminReports, updateAdminReportStatus } from '../services/reportService';
import { fetchMarketAnomalies, recalculateMarketAnomalies } from '../services/anomalyService';
import { formatExactVND } from '../utils/formatters';

const STATUS_TABS = [
  { key: '', label: 'Tất cả' },
  { key: 'pending', label: 'Chờ xử lý', color: 'bg-amber-100 text-amber-800' },
  { key: 'reviewed', label: 'Đang xem xét', color: 'bg-sky-100 text-sky-800' },
  { key: 'resolved', label: 'Đã giải quyết', color: 'bg-emerald-100 text-emerald-800' },
  { key: 'dismissed', label: 'Đã bác bỏ', color: 'bg-slate-100 text-slate-700' },
];

export function AdminPage() {
  const { user, isAdmin } = useSession();
  const [activeMainTab, setActiveMainTab] = useState('reports'); // 'reports' | 'anomalies'

  // State Báo cáo vi phạm
  const [reports, setReports] = useState([]);
  const [reportStatusFilter, setReportStatusFilter] = useState('pending');
  const [isReportsLoading, setIsReportsLoading] = useState(false);
  const [actionLoadingId, setActionLoadingId] = useState(null);

  // State Rủi ro & Bất thường (Anomalies)
  const [anomaliesData, setAnomaliesData] = useState(null);
  const [minRiskScore, setMinRiskScore] = useState(25);
  const [isAnomaliesLoading, setIsAnomaliesLoading] = useState(false);
  const [isRecalculating, setIsRecalculating] = useState(false);
  const [feedbackMsg, setFeedbackMsg] = useState(null);

  // Tải danh sách báo cáo vi phạm
  const loadReports = async (status = reportStatusFilter) => {
    setIsReportsLoading(true);
    try {
      const data = await fetchAdminReports(status || undefined);
      setReports(data || []);
    } catch (err) {
      console.error('Không thể tải báo cáo vi phạm:', err);
    } finally {
      setIsReportsLoading(false);
    }
  };

  // Tải danh sách rủi ro thị trường
  const loadAnomalies = async (score = minRiskScore) => {
    setIsAnomaliesLoading(true);
    try {
      const data = await fetchMarketAnomalies({ minRiskScore: score, limit: 50 });
      setAnomaliesData(data);
    } catch (err) {
      console.error('Không thể tải dữ liệu bất thường:', err);
    } finally {
      setIsAnomaliesLoading(false);
    }
  };

  useEffect(() => {
    if (isAdmin) {
      if (activeMainTab === 'reports') {
        loadReports(reportStatusFilter);
      } else {
        loadAnomalies(minRiskScore);
      }
    }
  }, [isAdmin, activeMainTab, reportStatusFilter, minRiskScore]);

  // Xử lý báo cáo
  const handleUpdateReport = async (reportId, newStatus, deactivateListing = false) => {
    setActionLoadingId(reportId);
    setFeedbackMsg(null);
    try {
      await updateAdminReportStatus(reportId, {
        status: newStatus,
        deactivateListing,
      });
      setFeedbackMsg({
        type: 'success',
        text: deactivateListing
          ? 'Đã duyệt báo cáo và ẩn tin đăng vi phạm khỏi thị trường!'
          : `Đã cập nhật trạng thái báo cáo thành "${newStatus}".`,
      });
      loadReports(reportStatusFilter);
    } catch (err) {
      setFeedbackMsg({
        type: 'error',
        text: err?.response?.data?.detail || 'Không thể cập nhật báo cáo.',
      });
    } finally {
      setActionLoadingId(null);
    }
  };

  // Kích hoạt tính lại Anomaly
  const handleRecalculateAnomalies = async () => {
    setIsRecalculating(true);
    setFeedbackMsg(null);
    try {
      const res = await recalculateMarketAnomalies();
      setFeedbackMsg({
        type: 'success',
        text: res.message || 'Đã cập nhật xong toàn bộ chỉ số bất thường.',
      });
      loadAnomalies(minRiskScore);
    } catch (err) {
      setFeedbackMsg({
        type: 'error',
        text: err?.response?.data?.detail || 'Không thể chạy lại quy trình tính toán.',
      });
    } finally {
      setIsRecalculating(false);
    }
  };

  if (!isAdmin) {
    return (
      <section className="mx-auto max-w-2xl rounded-2xl border border-red-200 bg-white p-8 text-center shadow-xs">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-red-50 text-red-600">
          <ShieldAlert className="h-8 w-8" />
        </div>
        <h1 className="mt-4 text-xl font-bold text-[#134E4A]">Yêu cầu Quyền Quản trị viên</h1>
        <p className="mt-2 text-sm text-[#475569]">
          Trang này dành riêng cho tài khoản Quản trị viên (Admin) để xử lý báo cáo vi phạm và giám sát điểm rủi ro tin đăng.
        </p>
        <div className="mt-6 flex justify-center gap-3">
          <Link
            to="/login"
            className="inline-flex items-center rounded-xl bg-[#0F766E] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#134E4A] transition-colors"
          >
            Đăng nhập tài khoản Admin
          </Link>
          <Link
            to="/"
            className="inline-flex items-center rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-[#134E4A] hover:bg-slate-50 transition-colors"
          >
            Về Trang chủ
          </Link>
        </div>
      </section>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Quản trị */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between rounded-2xl border border-teal-100 bg-white p-6 shadow-xs">
        <div>
          <div className="flex items-center gap-2">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#0F766E] text-white">
              <ShieldAlert className="h-4 w-4" />
            </span>
            <h1 className="text-xl font-bold text-[#134E4A]">Trung tâm Quản trị & Giám sát Vi phạm</h1>
          </div>
          <p className="mt-1 text-xs sm:text-sm text-[#475569]">
            Quản trị viên: <strong className="text-[#0F766E]">{user?.full_name || user?.email}</strong> · Học phần HTKDTM (Gói 2)
          </p>
        </div>

        {/* Tab chuyển đổi lớn */}
        <div className="flex rounded-xl bg-slate-100 p-1">
          <button
            type="button"
            onClick={() => setActiveMainTab('reports')}
            className={`inline-flex items-center gap-1.5 rounded-lg px-3.5 py-2 text-xs sm:text-sm font-semibold transition-all ${
              activeMainTab === 'reports'
                ? 'bg-white text-[#0F766E] shadow-xs'
                : 'text-[#475569] hover:text-[#134E4A]'
            }`}
          >
            <AlertTriangle className="h-4 w-4" />
            Báo cáo vi phạm ({reports.length})
          </button>
          <button
            type="button"
            onClick={() => setActiveMainTab('anomalies')}
            className={`inline-flex items-center gap-1.5 rounded-lg px-3.5 py-2 text-xs sm:text-sm font-semibold transition-all ${
              activeMainTab === 'anomalies'
                ? 'bg-white text-[#0F766E] shadow-xs'
                : 'text-[#475569] hover:text-[#134E4A]'
            }`}
          >
            <ShieldCheck className="h-4 w-4" />
            Rà soát Bất thường & Tin ảo
          </button>
        </div>
      </div>

      {/* Thông báo phản hồi */}
      {feedbackMsg && (
        <div
          className={`rounded-xl border px-4 py-3 text-xs sm:text-sm ${
            feedbackMsg.type === 'success'
              ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
              : 'border-red-200 bg-red-50 text-red-800'
          }`}
        >
          {feedbackMsg.text}
        </div>
      )}

      {/* TAB 1: BÁO CÁO VI PHẠM */}
      {activeMainTab === 'reports' && (
        <div className="space-y-4">
          {/* Bộ lọc trạng thái */}
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white p-3 shadow-xs">
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="text-xs font-semibold text-[#475569] mr-1 flex items-center gap-1">
                <Filter className="h-3.5 w-3.5" /> Trạng thái:
              </span>
              {STATUS_TABS.map((tab) => (
                <button
                  key={tab.key}
                  type="button"
                  onClick={() => setReportStatusFilter(tab.key)}
                  className={`rounded-lg px-3 py-1 text-xs font-medium transition-colors ${
                    reportStatusFilter === tab.key
                      ? 'bg-[#0F766E] text-white shadow-xs'
                      : 'bg-slate-100 text-[#475569] hover:bg-slate-200'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            <button
              type="button"
              onClick={() => loadReports(reportStatusFilter)}
              disabled={isReportsLoading}
              className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-[#134E4A] hover:bg-slate-50 transition-colors"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isReportsLoading ? 'animate-spin' : ''}`} />
              Làm mới
            </button>
          </div>

          {/* Danh sách báo cáo */}
          <div className="overflow-hidden rounded-2xl border border-teal-100 bg-white shadow-xs">
            {isReportsLoading ? (
              <div className="p-8 text-center text-sm text-[#475569]">
                <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-[#0F766E] border-t-transparent" />
                <p className="mt-2">Đang tải danh sách báo cáo...</p>
              </div>
            ) : reports.length === 0 ? (
              <div className="p-8 text-center text-sm text-[#475569]">
                Không có báo cáo nào ở trạng thái này.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs sm:text-sm">
                  <thead className="border-b border-slate-200 bg-slate-50/80 text-[#134E4A]">
                    <tr>
                      <th className="px-4 py-3 font-semibold">ID / Ngày gửi</th>
                      <th className="px-4 py-3 font-semibold">Tin đăng liên quan</th>
                      <th className="px-4 py-3 font-semibold">Lý do & Mô tả</th>
                      <th className="px-4 py-3 font-semibold">Trạng thái</th>
                      <th className="px-4 py-3 font-semibold text-right">Thao tác duyệt</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {reports.map((rep) => {
                      const isPending = rep.status === 'pending';
                      const isLoadingAction = actionLoadingId === rep.report_id;

                      return (
                        <tr key={rep.report_id} className="hover:bg-slate-50/60 transition-colors">
                          <td className="px-4 py-3 text-slate-500 whitespace-nowrap">
                            <span className="font-mono font-medium text-slate-700">#{rep.report_id}</span>
                            <div className="text-[11px] text-slate-400">
                              {rep.created_at ? new Date(rep.created_at).toLocaleString('vi-VN') : '—'}
                            </div>
                          </td>

                          <td className="px-4 py-3 max-w-xs">
                            <Link
                              to={`/listings/${rep.fact_id}`}
                              className="font-medium text-[#0F766E] hover:underline line-clamp-1"
                              title={rep.listing_title || rep.fact_id}
                            >
                              {rep.listing_title || `Phòng trọ (${rep.fact_id.slice(0, 8)}...)`}
                            </Link>
                            {rep.listing_url && (
                              <a
                                href={rep.listing_url}
                                target="_blank"
                                rel="noreferrer"
                                className="inline-flex items-center gap-0.5 text-[11px] text-slate-400 hover:text-slate-600 mt-0.5"
                              >
                                Link nguồn gốc <ExternalLink className="h-2.5 w-2.5" />
                              </a>
                            )}
                          </td>

                          <td className="px-4 py-3 max-w-sm">
                            <span className="inline-block rounded bg-red-50 px-2 py-0.5 text-xs font-semibold text-red-700 border border-red-200">
                              {rep.reason}
                            </span>
                            {rep.description && (
                              <p className="mt-1 text-slate-600 text-xs italic line-clamp-2">
                                "{rep.description}"
                              </p>
                            )}
                          </td>

                          <td className="px-4 py-3 whitespace-nowrap">
                            <span
                              className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${
                                rep.status === 'pending'
                                  ? 'bg-amber-100 text-amber-800'
                                  : rep.status === 'reviewed'
                                  ? 'bg-sky-100 text-sky-800'
                                  : rep.status === 'resolved'
                                  ? 'bg-emerald-100 text-emerald-800'
                                  : 'bg-slate-100 text-slate-600'
                              }`}
                            >
                              {rep.status === 'pending' && <Clock className="h-3 w-3" />}
                              {rep.status === 'resolved' && <CheckCircle2 className="h-3 w-3" />}
                              {rep.status === 'dismissed' && <XCircle className="h-3 w-3" />}
                              {rep.status === 'pending'
                                ? 'Chờ duyệt'
                                : rep.status === 'reviewed'
                                ? 'Đã xem'
                                : rep.status === 'resolved'
                                ? 'Đã ẩn tin'
                                : 'Đã bác bỏ'}
                            </span>
                          </td>

                          <td className="px-4 py-3 text-right whitespace-nowrap">
                            <div className="flex items-center justify-end gap-1.5">
                              {isPending && (
                                <button
                                  type="button"
                                  disabled={isLoadingAction}
                                  onClick={() => handleUpdateReport(rep.report_id, 'resolved', true)}
                                  className="inline-flex items-center gap-1 rounded-lg bg-red-600 px-2.5 py-1 text-xs font-semibold text-white hover:bg-red-700 transition-colors disabled:opacity-50"
                                  title="Duyệt báo cáo và ẩn tin đăng khỏi website"
                                >
                                  <EyeOff className="h-3.5 w-3.5" /> Ẩn tin vi phạm
                                </button>
                              )}

                              {isPending && (
                                <button
                                  type="button"
                                  disabled={isLoadingAction}
                                  onClick={() => handleUpdateReport(rep.report_id, 'dismissed', false)}
                                  className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2 py-1 text-xs font-medium text-slate-600 hover:bg-slate-50 transition-colors disabled:opacity-50"
                                  title="Báo cáo không chính xác, giữ nguyên tin"
                                >
                                  Bác bỏ
                                </button>
                              )}

                              {rep.status === 'dismissed' && (
                                <span className="text-xs text-slate-400">Đã hoàn tất</span>
                              )}
                              {rep.status === 'resolved' && (
                                <span className="text-xs text-emerald-600 font-medium">Đã ẩn tin</span>
                              )}
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: RÀ SOÁT BẤT THƯỜNG & TIN ẢO (ANOMALIES) */}
      {activeMainTab === 'anomalies' && (
        <div className="space-y-4">
          {/* Summary Metric Cards */}
          {anomaliesData?.summary && (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 sm:gap-4">
              <div className="rounded-xl border border-teal-100 bg-white p-4 shadow-xs">
                <p className="text-xs text-[#475569]">Tổng tin rà soát</p>
                <p className="mt-1 text-2xl font-bold text-[#134E4A]">
                  {anomaliesData.summary.total_listings}
                </p>
              </div>

              <div className="rounded-xl border border-red-200 bg-red-50/50 p-4 shadow-xs">
                <p className="text-xs text-red-600 font-medium">Rủi ro cao (≥ 50đ)</p>
                <p className="mt-1 text-2xl font-bold text-red-700">
                  {anomaliesData.summary.high_risk_count}
                </p>
              </div>

              <div className="rounded-xl border border-amber-200 bg-amber-50/50 p-4 shadow-xs">
                <p className="text-xs text-amber-700 font-medium">Rủi ro trung bình (25-49đ)</p>
                <p className="mt-1 text-2xl font-bold text-amber-800">
                  {anomaliesData.summary.medium_risk_count}
                </p>
              </div>

              <div className="rounded-xl border border-teal-100 bg-white p-4 shadow-xs">
                <p className="text-xs text-[#475569]">Độ đầy đủ thông tin TB</p>
                <p className="mt-1 text-2xl font-bold text-[#0F766E]">
                  {anomaliesData.summary.avg_completeness_score}
                  <span className="text-xs font-normal text-slate-500"> /100</span>
                </p>
              </div>
            </div>
          )}

          {/* Action & Filter Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white p-3 shadow-xs">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-[#475569]">Lọc theo điểm rủi ro tối thiểu:</span>
              <select
                value={minRiskScore}
                onChange={(e) => setMinRiskScore(Number(e.target.value))}
                className="rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-xs text-[#134E4A] font-medium focus:border-[#0F766E] focus:outline-none"
              >
                <option value={50}>Chỉ rủi ro cao (≥ 50 điểm)</option>
                <option value={25}>Rủi ro trung bình & cao (≥ 25 điểm)</option>
                <option value={0}>Tất cả các tin (≥ 0 điểm)</option>
              </select>
            </div>

            <button
              type="button"
              disabled={isRecalculating}
              onClick={handleRecalculateAnomalies}
              className="inline-flex items-center gap-1.5 rounded-lg bg-[#0F766E] px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-[#134E4A] transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isRecalculating ? 'animate-spin' : ''}`} />
              {isRecalculating ? 'Đang tính toán lại...' : 'Quét & Tính lại chỉ số thị trường'}
            </button>
          </div>

          {/* Danh sách tin có dấu hiệu bất thường */}
          <div className="overflow-hidden rounded-2xl border border-teal-100 bg-white shadow-xs">
            {isAnomaliesLoading ? (
              <div className="p-8 text-center text-sm text-[#475569]">
                <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-[#0F766E] border-t-transparent" />
                <p className="mt-2">Đang rà soát và tải dữ liệu bất thường...</p>
              </div>
            ) : !anomaliesData?.items || anomaliesData.items.length === 0 ? (
              <div className="p-8 text-center text-sm text-[#475569]">
                Không phát hiện tin đăng nào vượt ngưỡng rủi ro này.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs sm:text-sm">
                  <thead className="border-b border-slate-200 bg-slate-50/80 text-[#134E4A]">
                    <tr>
                      <th className="px-4 py-3 font-semibold">Điểm rủi ro</th>
                      <th className="px-4 py-3 font-semibold">Tin đăng</th>
                      <th className="px-4 py-3 font-semibold">Giá & Diện tích</th>
                      <th className="px-4 py-3 font-semibold">Chênh lệch khu vực</th>
                      <th className="px-4 py-3 font-semibold">Dấu hiệu bất thường (Flags)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {anomaliesData.items.map((item) => (
                      <tr key={item.fact_id} className="hover:bg-slate-50/60 transition-colors">
                        <td className="px-4 py-3 whitespace-nowrap">
                          <div
                            className={`inline-flex items-center gap-1 rounded-xl px-2.5 py-1 text-xs font-bold ${
                              item.risk_level === 'high'
                                ? 'bg-red-100 text-red-700 border border-red-200'
                                : item.risk_level === 'medium'
                                ? 'bg-amber-100 text-amber-800 border border-amber-200'
                                : 'bg-emerald-100 text-emerald-800'
                            }`}
                          >
                            <AlertTriangle className="h-3.5 w-3.5" />
                            {item.risk_score}đ
                          </div>
                          <div className="mt-0.5 text-[10px] text-slate-400">
                            Độ đầy đủ: {item.completeness_score}/100
                          </div>
                        </td>

                        <td className="px-4 py-3 max-w-xs">
                          <Link
                            to={`/listings/${item.fact_id}`}
                            className="font-medium text-[#0F766E] hover:underline line-clamp-1"
                            title={item.title}
                          >
                            {item.title}
                          </Link>
                          <div className="text-[11px] text-slate-500 mt-0.5">
                            {item.district || 'Hà Nội'} · {item.type_name || 'Phòng trọ'}
                          </div>
                        </td>

                        <td className="px-4 py-3 whitespace-nowrap">
                          <span className="font-semibold text-slate-800">
                            {formatExactVND(item.price)}
                          </span>
                          <div className="text-[11px] text-slate-500">
                            {item.area ? `${item.area} m²` : 'Chưa rõ diện tích'}
                          </div>
                        </td>

                        <td className="px-4 py-3 whitespace-nowrap">
                          <span
                            className={`font-semibold ${
                              item.price_diff_rate <= -30
                                ? 'text-red-600'
                                : item.price_diff_rate >= 50
                                ? 'text-amber-600'
                                : 'text-slate-600'
                            }`}
                          >
                            {item.price_diff_rate > 0 ? `+${item.price_diff_rate}%` : `${item.price_diff_rate}%`}
                          </span>
                          <div className="text-[10px] text-slate-400">so với cùng quận</div>
                        </td>

                        <td className="px-4 py-3 max-w-sm">
                          <div className="flex flex-wrap gap-1">
                            {item.risk_flags && item.risk_flags.length > 0 ? (
                              item.risk_flags.map((flag, idx) => (
                                <span
                                  key={idx}
                                  className="rounded bg-red-50 border border-red-100 px-1.5 py-0.5 text-[10px] font-medium text-red-700"
                                >
                                  {flag}
                                </span>
                              ))
                            ) : (
                              <span className="text-xs text-slate-400">Không có cảnh báo</span>
                            )}
                            {item.report_count > 0 && (
                              <span className="rounded bg-purple-50 border border-purple-200 px-1.5 py-0.5 text-[10px] font-bold text-purple-700">
                                {item.report_count} báo cáo vi phạm
                              </span>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
