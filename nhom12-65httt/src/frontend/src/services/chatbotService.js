import { apiClient } from './apiClient';

/**
 * Gửi câu hỏi ngôn ngữ tự nhiên tới Chatbot BI Text-to-SQL backend
 * @param {string} query - Câu hỏi tiếng Việt của người dùng
 * @param {string} sessionId - ID phiên làm việc
 * @returns {Promise<{
 *   query: string,
 *   sql: string,
 *   chart_type: 'bar' | 'line' | 'pie' | 'table',
 *   columns: string[],
 *   rows: Array<Record<string, any>>,
 *   total_rows: int,
 *   insight: string,
 *   role: string
 * }>}
 */
export async function queryChatbot(query, sessionId) {
  const { data } = await apiClient.post('/api/chatbot/query', {
    query,
    session_id: sessionId,
  });
  return data;
}
