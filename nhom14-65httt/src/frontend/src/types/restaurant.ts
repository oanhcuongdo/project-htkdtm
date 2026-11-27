/** Giờ HH:MM theo Việt Nam; các cờ khả dụng được tính tại máy chủ. */
export interface RestaurantPublic {
  id: number;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  delivery_radius_km: number;
  opens_at: string;
  closes_at: string;
  accepting_orders: boolean;
  is_open: boolean;
  can_receive_orders: boolean;
}
