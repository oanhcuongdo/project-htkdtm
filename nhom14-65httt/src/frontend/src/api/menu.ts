import { apiClient } from "./client";
import { queryString, type ReadOptions } from "./query";
import type { Page, PaginationQuery } from "../types/common";
import type {
  CanonicalDishPublic,
  IngredientPublic,
  MenuItemPublic,
} from "../types/menu";

export function getMenuItem(
  id: number,
  { signal }: ReadOptions = {},
): Promise<MenuItemPublic> {
  return apiClient.request(`/menu-items/${id}`, {
    authenticated: false,
    signal,
  });
}

/** Endpoint thực đơn trả mảng, không có total như endpoint danh mục. */
export function getRestaurantMenu(
  id: number,
  { offset, limit }: PaginationQuery = {},
  { signal }: ReadOptions = {},
): Promise<MenuItemPublic[]> {
  return apiClient.request(
    `/restaurants/${id}/menu${queryString({ offset, limit })}`,
    { authenticated: false, signal },
  );
}

export function listCanonicalDishes(
  { offset, limit }: PaginationQuery = {},
  { signal }: ReadOptions = {},
): Promise<Page<CanonicalDishPublic>> {
  return apiClient.request(
    `/canonical-dishes${queryString({ offset, limit })}`,
    {
      authenticated: false,
      signal,
    },
  );
}

export function listIngredients(
  { offset, limit }: PaginationQuery = {},
  { signal }: ReadOptions = {},
): Promise<Page<IngredientPublic>> {
  return apiClient.request(`/ingredients${queryString({ offset, limit })}`, {
    authenticated: false,
    signal,
  });
}
