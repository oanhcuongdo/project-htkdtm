import type { PaginationQuery } from "./common";
import type { MenuItemPublic } from "./menu";
import type { RestaurantPublic } from "./restaurant";

export interface SearchQuery extends PaginationQuery {
  lat: number;
  lng: number;
  q?: string;
  /** Km; mặc định máy chủ 5, tối đa 50. */
  radius?: number;
}

export interface DishSearchResult extends MenuItemPublic {
  distance_km: number;
  restaurant: RestaurantPublic;
}

export interface RestaurantSearchResult extends RestaurantPublic {
  distance_km: number;
}
