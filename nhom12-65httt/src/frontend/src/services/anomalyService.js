import { apiClient } from './apiClient';

/**
 * Lấy danh sách tin có dấu hiệu bất thường / rủi ro tin ảo (Dành cho Quản trị viên)
 * @param {object} params
 * @param {number} [params.minRiskScore=25.0]
 * @param {number} [params.limit=50]
 */
export async function fetchMarketAnomalies({ minRiskScore = 25.0, limit = 50 } = {}) {
  const { data } = await apiClient.get('/api/admin/anomalies', {
    params: {
      min_risk_score: minRiskScore,
      limit,
    },
  });
  return data;
}

/**
 * Kích hoạt backend rà soát và tính lại toàn bộ chỉ số bất thường trên thị trường
 */
export async function recalculateMarketAnomalies() {
  const { data } = await apiClient.post('/api/admin/anomalies/recalculate');
  return data;
}
