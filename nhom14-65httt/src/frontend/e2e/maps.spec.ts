import { test, expect } from "@playwright/test";
import { restaurant } from "../tests/fixtures/catalog";
test("bản đồ tải theo yêu cầu, chỉ đường đúng quán và không chặn thực đơn", async ({
  page,
}, info) => {
  await page.route("**/api/v1/restaurants/3", (route) =>
    route.fulfill({ json: restaurant }),
  );
  await page.route("**/api/v1/restaurants/3/menu?*", (route) =>
    route.fulfill({ json: [] }),
  );
  let requests = 0;
  await page.route(
    "https://www.openstreetmap.org/export/embed.html?*",
    (route) => {
      requests++;
      expect(new URL(route.request().url()).searchParams.get("marker")).toBe(
        "21,105",
      );
      return route.abort("failed");
    },
  );
  await page.goto("/restaurants/3");
  await expect(
    page.getByRole("button", { name: "Xem bản đồ quán" }),
  ).toBeVisible();
  expect(requests).toBe(0);
  await expect(page.locator("iframe")).toHaveCount(0);
  const directions = page.getByRole("link", {
    name: "Chỉ đường đến quán (tab mới)",
  });
  expect(
    new URL((await directions.getAttribute("href"))!).searchParams.get(
      "destination",
    ),
  ).toBe("21,105");
  await page.getByRole("button", { name: "Xem bản đồ quán" }).click();
  await expect(
    page.getByTitle(`Bản đồ vị trí ${restaurant.name}`),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Quán chưa có món đang bán" }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "mở OpenStreetMap ở tab mới" }),
  ).toBeVisible();
  await expect.poll(() => requests).toBe(1);
  for (const width of [360, 1280]) {
    await page.setViewportSize({ width, height: 900 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    await page.screenshot({
      path: info.outputPath(`map-fallback-${width}.png`),
      fullPage: true,
    });
  }
  await page.getByRole("button", { name: "Ẩn bản đồ" }).click();
  await expect(page.locator("iframe")).toHaveCount(0);
});
