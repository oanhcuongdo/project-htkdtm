import { apiClient } from './apiClient';

export async function submitListingReport({ factId, reporterSessionId, reason, description }) {
  const { data } = await apiClient.post('/api/reports', {
    fact_id: factId,
    reporter_session_id: reporterSessionId,
    reason,
    description,
  });
  return data;
}

export async function fetchAdminReports(statusFilter) {
  const params = statusFilter ? { status: statusFilter } : {};
  const { data } = await apiClient.get('/api/admin/reports', { params });
  return data;
}

export async function updateAdminReportStatus(reportId, { status, deactivateListing = false }) {
  const { data } = await apiClient.patch(`/api/admin/reports/${reportId}`, {
    status,
    deactivate_listing: deactivateListing,
  });
  return data;
}
