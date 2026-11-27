import { test, expect } from "@playwright/test";

for (const role of ["customer", "vendor"] as const) {
  test(`đăng ký, đăng nhập, tải lại và đăng xuất ${role} với backend thật`, async ({
    page,
  }) => {
    const failures: string[] = [];
    page.on("pageerror", (error) => failures.push(error.message));
    const email = `auth-${role}-${Date.now()}@example.vn`;
    const password = "Mat khau e2e 123!";
    await page.goto("/register");
    await page.getByLabel("Họ và tên").fill("Người dùng kiểm thử");
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Mật khẩu", { exact: true }).fill(password);
    await page.getByLabel("Xác nhận mật khẩu", { exact: true }).fill(password);
    await page.getByLabel("Loại tài khoản").selectOption(role);
    await page.getByRole("checkbox", { name: /Tôi đồng ý/ }).check();
    await page.getByRole("button", { name: "Tạo tài khoản" }).click();
    await expect(page.getByRole("status")).toHaveText(
      "Đã tạo tài khoản. Bạn có thể đăng nhập ngay.",
    );
    await expect(page.getByLabel("Email")).toHaveValue(email);
    await page.getByLabel("Mật khẩu", { exact: true }).fill("sai-mat-khau");
    await page.getByRole("button", { name: "Đăng nhập", exact: true }).click();
    await expect(page.getByRole("alert")).toHaveText(
      "Email hoặc mật khẩu không đúng.",
    );
    await page.getByLabel("Mật khẩu", { exact: true }).fill(password);
    if (role === "vendor")
      await page.getByRole("checkbox", { name: "Ghi nhớ đăng nhập" }).uncheck();
    await page.getByLabel("Mật khẩu", { exact: true }).press("Enter");
    const destination = role === "vendor" ? "/vendor" : "/account";
    await expect(page).toHaveURL(new RegExp(destination + "$"));
    expect(
      await page.evaluate(() => ({
        local: Boolean(localStorage.getItem("viviet.auth.v1")),
        session: Boolean(sessionStorage.getItem("viviet.auth.v1")),
      })),
    ).toEqual({ local: role === "customer", session: role === "vendor" });
    await expect(
      page.getByRole("heading", { name: "Chào Người dùng kiểm thử." }),
    ).toBeVisible();
    await page.reload();
    await expect(page.getByText(email, { exact: true })).toBeVisible();
    await page.goto("/admin");
    await expect(
      page.getByRole("heading", { name: "Trang này dành cho vai trò khác." }),
    ).toBeVisible();
    await page.goto(destination);
    await expect(page.getByText(email, { exact: true })).toBeVisible();
    await page.getByRole("button", { name: "Đăng xuất" }).click();
    await expect(page).toHaveURL(/\/login$/);
    await page.goto(destination);
    await expect(page).toHaveURL(/\/login$/);
    expect(failures).toEqual([]);
  });
}

test("giao diện đăng nhập/đăng ký trên desktop và điện thoại không tràn ngang", async ({
  page,
}, info) => {
  for (const viewport of [
    { width: 1280, height: 900 },
    { width: 390, height: 844 },
    { width: 360, height: 800 },
    { width: 768, height: 1024 },
  ]) {
    await page.setViewportSize(viewport);
    for (const path of ["/login", "/register"]) {
      await page.goto(path);
      await expect(page.getByLabel("Email")).toBeVisible();
      await page.evaluate(() => document.fonts.ready);
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= window.innerWidth,
        ),
      ).toBe(true);
      await page.screenshot({
        path: info.outputPath(`${path.slice(1)}-${viewport.width}.png`),
        fullPage: true,
      });
    }
  }
});

test("hiện/ẩn mật khẩu, hộp thoại, bàn phím và trạng thái lỗi ở 360px", async ({
  page,
}, info) => {
  await page.setViewportSize({ width: 360, height: 800 });
  await page.goto("/login");
  await page.getByLabel("Email").focus();
  await page.keyboard.press("Tab");
  await expect(page.getByLabel("Mật khẩu", { exact: true })).toBeFocused();
  await page.getByLabel("Mật khẩu", { exact: true }).fill("mat-khau-thu");
  await page.keyboard.press("Tab");
  const toggle = page.getByRole("button", {
    name: "Hiện mật khẩu",
    exact: true,
  });
  await expect(toggle).toBeFocused();
  const toggleBox = await toggle.boundingBox();
  expect(toggleBox!.height).toBeGreaterThanOrEqual(48);
  expect(toggleBox!.width).toBeGreaterThanOrEqual(48);
  await page.keyboard.press("Enter");
  await expect(page.getByLabel("Mật khẩu", { exact: true })).toHaveAttribute(
    "type",
    "text",
  );
  await page.getByRole("button", { name: "Quên mật khẩu?" }).click();
  await expect(
    page.getByRole("dialog", { name: "Hỗ trợ đăng nhập" }),
  ).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Quên mật khẩu?" }),
  ).toBeFocused();
  await page.getByRole("button", { name: "Đăng nhập", exact: true }).click();
  await expect(page.getByLabel("Email")).toBeFocused();
  await expect(page.getByText("Vui lòng nhập email.")).toBeVisible();
  await page.screenshot({
    path: info.outputPath("login-error-360.png"),
    fullPage: true,
  });
  await page.goto("/register");
  await page
    .getByRole("button", { name: "Điều khoản sử dụng", exact: true })
    .first()
    .click();
  await expect(
    page.getByRole("dialog", { name: "Điều khoản sử dụng" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Đã hiểu" }).click();
  await expect(
    page.getByRole("checkbox", { name: /Tôi đồng ý/ }),
  ).not.toBeChecked();
  await page.emulateMedia({ reducedMotion: "reduce" });
  expect(
    await page
      .locator(".auth-primary-button")
      .evaluate((button) => getComputedStyle(button).transitionDuration),
  ).toBe("0s");
  await expect(page.getByRole("button", { name: /Google/ })).toHaveCount(0);
});
