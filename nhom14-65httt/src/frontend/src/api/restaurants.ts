import { apiClient } from "./client";
import { queryString, type ReadOptions } from "./query";
import type { Page, PaginationQuery } from "../types/common";
import type { RestaurantPublic } from "../types/restaurant";

export function listRestaurants(
  { offset, limit }: PaginationQuery = {},
  { signal }: ReadOptions = {},
): Promise<Page<RestaurantPublic>> {
  return apiClient.request(`/restaurants/${queryString({ offset, limit })}`, {
    authenticated: false,
    signal,
  });
}

export function getRestaurant(
  id: number,
  { signal }: ReadOptions = {},
): Promise<RestaurantPublic> {
  return apiClient.request(`/restaurants/${id}`, {
    authenticated: false,
    signal,
  });
}
