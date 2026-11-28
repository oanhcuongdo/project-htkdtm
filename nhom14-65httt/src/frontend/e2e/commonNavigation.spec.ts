import { test, expect } from "@playwright/test";

test("404 có đường về và xóa vị trí xóa nội dung nhập dự phòng", async ({
  page,
}) => {
  await page.route("**/api/v1/search/dishes?*", (route) =>
    route.fulfill({ json: { items: [], total: 0, offset: 0, limit: 12 } }),
  );
  await page.goto("/duong-dan-khong-ton-tai");
  await expect(
    page.getByRole("heading", { name: "Chưa tìm thấy trang bạn cần." }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Về trang chủ", exact: true }).click();
  await expect(page).toHaveURL(/\/$/);
  await page.getByRole("link", { name: "Tìm món, quán", exact: true }).click();
  await page.getByLabel("Tên địa điểm (không bắt buộc)").fill("Cổng trường");
  await page.getByLabel("Vĩ độ", { exact: true }).fill("21");
  await page.getByLabel("Kinh độ", { exact: true }).fill("105");
  await page.getByRole("button", { name: "Dùng tọa độ này" }).click();
  await page.getByRole("button", { name: "Xóa vị trí" }).click();
  await expect(page.getByLabel("Vĩ độ", { exact: true })).toHaveValue("");
  await expect(page.getByLabel("Kinh độ", { exact: true })).toHaveValue("");
  await expect(page.getByLabel("Tên địa điểm (không bắt buộc)")).toHaveValue(
    "",
  );
});
