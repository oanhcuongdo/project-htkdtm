import { apiClient } from './apiClient';

/**
 * Lấy dữ liệu tổng hợp 3 nhóm Insight BI từ Supabase qua Backend
 */
export async function fetchMarketBIOverview() {
  const { data } = await apiClient.get('/api/bi/overview');
  return data;
}
