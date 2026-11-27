/** Phân trang offset/limit theo hợp đồng backend. */
export interface PaginationQuery {
  offset?: number;
  limit?: number;
}

export interface Page<T> {
  items: T[];
  total: number;
  offset: number;
  limit: number;
}
