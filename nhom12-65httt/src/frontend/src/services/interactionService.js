import { apiClient } from './apiClient';

export async function trackInteraction({ sessionId, factId, actionType, metadata = {} }) {
  const { data } = await apiClient.post('/api/interactions', {
    session_id: sessionId,
    fact_id: factId,
    action_type: actionType,
    metadata,
  });
  return data;
}

export async function fetchWishlist(sessionId) {
  const { data } = await apiClient.get('/api/wishlist', {
    params: { session_id: sessionId },
  });
  return data;
}

export async function saveSearchHistory({ sessionId, rawQuery, parsedFilters = {}, resultsCount = 0 }) {
  const { data } = await apiClient.post('/api/search-history', {
    session_id: sessionId,
    raw_query: rawQuery,
    parsed_filters: parsedFilters,
    results_count: resultsCount,
  });
  return data;
}

export async function fetchSearchHistory(sessionId) {
  const { data } = await apiClient.get('/api/search-history', {
    params: { session_id: sessionId },
  });
  return data;
}
