import { apiClient } from "./client";
import { queryString, type ReadOptions } from "./query";
import type { Page } from "../types/common";
import type {
  DishSearchResult,
  RestaurantSearchResult,
  SearchQuery,
} from "../types/search";

function searchQuery({ lat, lng, q, radius, offset, limit }: SearchQuery) {
  return queryString({ lat, lng, q, radius, offset, limit });
}

export function searchDishes(
  params: SearchQuery,
  { signal }: ReadOptions = {},
): Promise<Page<DishSearchResult>> {
  return apiClient.request(`/search/dishes${searchQuery(params)}`, {
    authenticated: false,
    signal,
  });
}

export function searchRestaurants(
  params: SearchQuery,
  { signal }: ReadOptions = {},
): Promise<Page<RestaurantSearchResult>> {
  return apiClient.request(`/search/restaurants${searchQuery(params)}`, {
    authenticated: false,
    signal,
  });
}
