export interface IngredientPublic {
  id: number;
  name: string;
}

export interface CanonicalDishPublic {
  id: number;
  name: string;
  region: string;
  method: string;
  spice_level: number;
  ingredients: string[];
  labels: string[];
}

/** Giá nguyên VNĐ; nguyên liệu thực tế tách khỏi đặc trưng của món chuẩn. */
export interface MenuItemPublic {
  id: number;
  restaurant_id: number;
  restaurant_name: string;
  canonical_dish_id: number;
  name: string;
  price: number;
  is_available: boolean;
  ingredients_verified: boolean;
  canonical_dish: CanonicalDishPublic;
  ingredients: IngredientPublic[];
}
