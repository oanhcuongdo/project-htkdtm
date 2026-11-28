import { test, expect } from "@playwright/test";

const restaurant = {
  id: 3,
  name: "Bếp Việt",
  address: "Số 1, phố Trần Phú",
  latitude: 21,
  longitude: 105,
  delivery_radius_km: 5,
  opens_at: "08:00",
  closes_at: "22:00",
  accepting_orders: true,
  is_open: true,
  can_receive_orders: true,
  distance_km: 1.25,
};
const dish = {
  id: 9,
  name: "Phở bò tái",
  restaurant_id: 3,
  restaurant_name: restaurant.name,
  canonical_dish_id: 2,
  price: 35000,
  is_available: true,
  ingredients_verified: true,
  ingredients: [
    { id: 1, name: "bò" },
    { id: 2, name: "hành" },
  ],
  canonical_dish: {
    id: 2,
    name: "Phở bò",
    region: "Bắc",
    method: "Nấu",
    spice_level: 0,
    ingredients: ["bò"],
    labels: [],
  },
  distance_km: 1.25,
  restaurant,
};

test("tìm món/quán, đổi trang, lỗi và thử lại với API kiểm soát", async ({
  page,
}) => {
  let requests = 0,
    fail = true;
  await page.route("**/api/v1/search/**", async (route) => {
    requests++;
    expect(route.request().headers()["authorization"]).toBeUndefined();
    const url = new URL(route.request().url());
    expect(url.searchParams.get("lat")).toBe("0");
    expect(url.searchParams.get("lng")).toBe("0");
    if (fail) {
      fail = false;
      return route.fulfill({
        status: 503,
        json: {
          error: { code: "UNAVAILABLE", message: "Chưa tải được dữ liệu." },
        },
      });
    }
    const offset = Number(url.searchParams.get("offset"));
    const mode = url.pathname.endsWith("/restaurants");
    const empty = url.searchParams.get("q") === "không có";
    return route.fulfill({
      json: {
        items: empty
          ? []
          : mode
            ? [restaurant]
            : Array.from({ length: offset ? 1 : 12 }, (_, index) => ({
                ...dish,
                id: index + offset + 1,
                name: offset ? "Món trang sau" : dish.name,
              })),
        total: empty ? 0 : mode ? 1 : 13,
        offset,
        limit: 12,
      },
    });
  });
  await page.goto("/search");
  expect(requests).toBe(0);
  await page.getByLabel("Vĩ độ", { exact: true }).fill("0");
  await page.getByLabel("Kinh độ", { exact: true }).fill("0");
  await page.getByRole("button", { name: "Dùng tọa độ này" }).click();
  await expect(page.getByRole("alert")).toHaveText("Chưa tải được dữ liệu.");
  await page.getByRole("button", { name: "Thử lại" }).click();
  await expect(page.getByRole("heading", { name: dish.name })).toHaveCount(12);
  const mapPicker = page.getByLabel("Quán cần xem vị trí");
  await expect(mapPicker.locator("option")).toHaveCount(2);
  await mapPicker.selectOption("3");
  await expect(page.locator("iframe")).toHaveCount(0);
  await page.route("https://www.openstreetmap.org/**", (route) =>
    route.abort(),
  );
  await page.getByRole("button", { name: "Xem bản đồ quán" }).click();
  await expect(page.locator("iframe")).toHaveCount(1);
  await page.getByRole("button", { name: "Trang sau" }).click();
  await expect(
    page.getByRole("heading", { name: "Món trang sau" }),
  ).toBeVisible();
  await expect(mapPicker).toHaveValue("");
  await expect(page.locator("iframe")).toHaveCount(0);
  await mapPicker.selectOption("3");
  await page.getByRole("button", { name: "Quán ăn", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: restaurant.name }),
  ).toBeVisible();
  await expect(mapPicker).toHaveValue("");
  await page.getByLabel("Bạn muốn tìm gì?").fill("không có");
  await page.getByLabel("Bạn muốn tìm gì?").press("Enter");
  await expect(
    page.getByRole("heading", { name: "Chưa có kết quả phù hợp" }),
  ).toBeVisible();
  await expect(mapPicker).toHaveCount(0);
  await page.getByRole("button", { name: "Xóa vị trí" }).click();
  await expect(
    page.getByRole("heading", { name: "Chọn vị trí để bắt đầu" }),
  ).toBeVisible();
});

test("từ chối quyền vị trí vẫn tìm thủ công, responsive bốn kích thước", async ({
  page,
}, info) => {
  await page.addInitScript(() =>
    Object.defineProperty(navigator, "geolocation", {
      configurable: true,
      value: {
        getCurrentPosition: (
          _ok: unknown,
          fail: (error: { code: number }) => void,
        ) => fail({ code: 1 }),
      },
    }),
  );
  await page.route("**/api/v1/search/**", (route) =>
    route.fulfill({
      json: {
        items: [
          dish,
          {
            ...dish,
            id: 10,
            name: "Cơm bò xào nấm",
            price: 45000,
            canonical_dish: { ...dish.canonical_dish, region: "Nam" },
            restaurant: {
              ...restaurant,
              is_open: false,
              can_receive_orders: false,
            },
          },
        ],
        total: 2,
        offset: 0,
        limit: 12,
      },
    }),
  );
  await page.goto("/search");
  await page.getByRole("button", { name: "Dùng vị trí hiện tại" }).click();
  await expect(page.getByRole("alert")).toContainText("chưa cấp quyền");
  await page.getByLabel("Tên địa điểm (không bắt buộc)").fill("Cổng trường");
  await page.getByLabel("Vĩ độ", { exact: true }).fill("21.0285");
  await page.getByLabel("Kinh độ", { exact: true }).fill("105.8542");
  await page.getByRole("button", { name: "Dùng tọa độ này" }).click();
  await expect(page.getByRole("heading", { name: dish.name })).toBeVisible();
  await page.getByLabel("Quán cần xem vị trí").selectOption("3");
  for (const width of [360, 390, 768, 1280]) {
    await page.setViewportSize({ width, height: 900 });
    await page.evaluate(() => document.fonts.ready);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    await page.screenshot({
      path: info.outputPath(`search-${width}.png`),
      fullPage: true,
    });
  }
});

test("bản đồ đổi quán, đổi vị trí và trạng thái nhận đơn từ máy chủ", async ({
  page,
}) => {
  const other = {
    ...restaurant,
    id: 4,
    name: "Quán thứ hai",
    latitude: 22,
    longitude: 106,
    can_receive_orders: false,
  };
  await page.route("**/api/v1/search/**", (route) =>
    route.fulfill({
      json: {
        items: [restaurant, other],
        total: 2,
        offset: 0,
        limit: 12,
      },
    }),
  );
  await page.route("https://www.openstreetmap.org/**", (route) =>
    route.abort(),
  );
  await page.goto("/search");
  await page.getByRole("button", { name: "Quán ăn", exact: true }).click();
  await page.getByLabel("Vĩ độ", { exact: true }).fill("21");
  await page.getByLabel("Kinh độ", { exact: true }).fill("105");
  await page.getByRole("button", { name: "Dùng tọa độ này" }).click();
  await expect(
    page.getByText("Hiện chưa thể nhận đơn", { exact: true }),
  ).toBeVisible();
  const picker = page.getByLabel("Quán cần xem vị trí");
  await picker.selectOption("3");
  await page.getByRole("button", { name: "Xem bản đồ quán" }).click();
  await expect(page.locator("iframe")).toHaveAttribute(
    "title",
    `Bản đồ vị trí ${restaurant.name}`,
  );
  await picker.selectOption("4");
  await expect(page.locator("iframe")).toHaveCount(0);
  await expect(
    page.getByRole("link", { name: "Chỉ đường đến quán (tab mới)" }),
  ).toHaveAttribute("href", /destination=22%2C106/);
  await page.getByText("Nhập tọa độ thủ công", { exact: true }).click();
  await page.getByLabel("Vĩ độ", { exact: true }).fill("22");
  await page.getByRole("button", { name: "Dùng tọa độ này" }).click();
  await expect(picker).toHaveValue("");
  await expect(page.locator("iframe")).toHaveCount(0);
});
