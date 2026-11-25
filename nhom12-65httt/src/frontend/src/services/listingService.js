import { apiClient } from './apiClient';

export async function fetchListings(params = {}) {
  const cleanParams = Object.fromEntries(
    Object.entries(params).filter(([, v]) => v !== '' && v !== null && v !== undefined)
  );
  const { data } = await apiClient.get('/api/listings', { params: cleanParams });
  return data;
}

export async function fetchListingDetail(factId) {
  const { data } = await apiClient.get(`/api/listings/${factId}`);
  return data;
}

export async function fetchComparedListings(ids = []) {
  const { data } = await apiClient.get('/api/listings/compare', {
    params: { ids: ids.join(',') },
  });
  return data;
}

export async function fetchDistrictStats() {
  const { data } = await apiClient.get('/api/listings/stats/districts');
  return data;
}
