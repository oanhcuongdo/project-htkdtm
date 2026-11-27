import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { apiClient, ApiError, AUTH_STORAGE_KEY } from "../src/api/client";
import {
  getMenuItem,
  getRestaurantMenu,
  listCanonicalDishes,
  listIngredients,
} from "../src/api/menu";
import { getRestaurant, listRestaurants } from "../src/api/restaurants";
import { searchDishes, searchRestaurants } from "../src/api/search";

const fetcher = vi.fn<typeof fetch>();
const page = { items: [], total: 0, offset: 0, limit: 20 };

beforeEach(() => {
  fetcher.mockReset();
  vi.stubGlobal("fetch", fetcher);
  localStorage.setItem(
    AUTH_STORAGE_KEY,
    JSON.stringify({ access_token: "private", refresh_token: "refresh" }),
  );
  apiClient.syncFromStorage();
});

afterEach(() => {
  apiClient.logout();
  vi.unstubAllGlobals();
});

it.each([
  ["danh sách quán", () => listRestaurants(), "/restaurants/", page],
  ["chi tiết quán", () => getRestaurant(7), "/restaurants/7", { id: 7 }],
  ["chi tiết món", () => getMenuItem(9), "/menu-items/9", { id: 9 }],
  ["thực đơn", () => getRestaurantMenu(7), "/restaurants/7/menu", []],
  ["món chuẩn", () => listCanonicalDishes(), "/canonical-dishes", page],
  ["nguyên liệu", () => listIngredients(), "/ingredients", page],
  [
    "tìm món",
    () => searchDishes({ lat: 0, lng: 0 }),
    "/search/dishes?lat=0&lng=0",
    page,
  ],
  [
    "tìm quán",
    () => searchRestaurants({ lat: 0, lng: 0 }),
    "/search/restaurants?lat=0&lng=0",
    page,
  ],
] as const)(
  "%s gọi đúng endpoint công khai dù đang đăng nhập",
  async (_, call, path, body) => {
    fetcher.mockResolvedValue(new Response(JSON.stringify(body)));
    expect(await call()).toEqual(body);
    expect(fetcher).toHaveBeenCalledOnce();
    const [url, options] = fetcher.mock.calls[0];
    expect(url).toBe(`/api/v1${path}`);
    expect(new Headers(options?.headers).has("Authorization")).toBe(false);
    expect(options?.credentials).toBe("omit");
    expect(options?.body).toBeUndefined();
  },
);

it("mã hóa tiếng Việt và ký tự &/? để không tạo query ngoài ý muốn", async () => {
  fetcher.mockResolvedValue(new Response(JSON.stringify(page)));
  const params = {
    lat: 21.0285,
    lng: 105.8542,
    q: "phở & cơm?/",
    radius: 2,
    offset: 0,
    limit: 5,
  };
  await searchDishes(params);
  const url = new URL(String(fetcher.mock.calls[0][0]), "https://example.vn");
  expect(Object.fromEntries(url.searchParams)).toEqual({
    lat: "21.0285",
    lng: "105.8542",
    q: params.q,
    radius: "2",
    offset: "0",
    limit: "5",
  });
  expect(params.q).toBe("phở & cơm?/");
});

it.each([
  [() => listRestaurants({ offset: 0, limit: 10 }), "/restaurants/"],
  [() => getRestaurantMenu(3, { offset: 0, limit: 10 }), "/restaurants/3/menu"],
  [() => listCanonicalDishes({ offset: 0, limit: 10 }), "/canonical-dishes"],
  [() => listIngredients({ offset: 0, limit: 10 }), "/ingredients"],
] as const)("giữ offset 0 và phân trang ở %s", async (call, path) => {
  fetcher.mockResolvedValue(new Response(JSON.stringify(page)));
  await call();
  expect(fetcher.mock.calls[0][0]).toBe(`/api/v1${path}?offset=0&limit=10`);
});

it("giữ lỗi nghiệp vụ và không refresh cho API công khai", async () => {
  fetcher.mockResolvedValue(
    new Response(
      JSON.stringify({
        error: {
          code: "NOT_FOUND",
          message: "Không tìm thấy món.",
          details: {},
        },
      }),
      { status: 404 },
    ),
  );
  await expect(getMenuItem(999)).rejects.toMatchObject({
    name: "ApiError",
    status: 404,
    code: "NOT_FOUND",
    message: "Không tìm thấy món.",
  } satisfies Partial<ApiError>);
  expect(fetcher).toHaveBeenCalledOnce();
  expect(apiClient.hasSession).toBe(true);
});

it("truyền hủy yêu cầu xuống fetch khi người dùng đổi tìm kiếm", async () => {
  const controller = new AbortController();
  fetcher.mockImplementation(
    (_url, options) =>
      new Promise((_resolve, reject) => {
        options?.signal?.addEventListener(
          "abort",
          () => reject(new DOMException("Đã hủy", "AbortError")),
          { once: true },
        );
      }),
  );
  const request = searchRestaurants(
    { lat: 10, lng: 106 },
    { signal: controller.signal },
  );
  controller.abort();
  await expect(request).rejects.toMatchObject({ name: "AbortError" });
  expect(fetcher.mock.calls[0][1]?.signal?.aborted).toBe(true);
});
