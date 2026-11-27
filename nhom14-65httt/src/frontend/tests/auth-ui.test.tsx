import { afterEach, beforeAll, beforeEach, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import App from "../src/App";
import { AUTH_STORAGE_KEY, apiClient } from "../src/api/client";

const user = {
  id: 1,
  email: "khach@example.vn",
  full_name: "Nguyễn Văn A",
  role: "customer",
  is_simulated: false,
  created_at: "2026-11-26T10:00:00Z",
};
const tokens = { access_token: "test-access", refresh_token: "test-refresh" };
const result = { ...tokens, user, token_type: "bearer", expires_in: 3600 };
const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status });
const fetcher = vi.fn<typeof fetch>();
beforeAll(() => {
  HTMLDialogElement.prototype.showModal = function () {
    this.open = true;
  };
  HTMLDialogElement.prototype.close = function () {
    this.open = false;
  };
});
function open(path: string) {
  return render(
    <MemoryRouter
      initialEntries={[path]}
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <App />
    </MemoryRouter>,
  );
}
function savedSession() {
  localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(tokens));
  apiClient.syncFromStorage();
}
beforeEach(() => {
  apiClient.logout();
  localStorage.clear();
  sessionStorage.clear();
  fetcher.mockReset();
  vi.stubGlobal("fetch", fetcher);
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

it("bảo vệ trang tài khoản và quay lại sau đăng nhập", async () => {
  fetcher.mockResolvedValue(json(result));
  const browser = userEvent.setup();
  open("/account");
  await screen.findByRole("heading", { name: "Chào mừng bạn trở lại" });
  await browser.type(screen.getByLabelText("Email"), user.email);
  await browser.type(screen.getByLabelText("Mật khẩu"), "password123");
  await browser.click(screen.getByRole("button", { name: "Đăng nhập" }));
  await screen.findByRole("heading", { name: "Chào Nguyễn Văn A." });
  expect(screen.getByText(user.email)).toBeTruthy();
  expect(JSON.parse(localStorage.getItem(AUTH_STORAGE_KEY)!)).toEqual(tokens);
  await browser.click(screen.getByRole("button", { name: "Đăng xuất" }));
  await screen.findByRole("heading", { name: "Chào mừng bạn trở lại" });
  expect(localStorage.getItem(AUTH_STORAGE_KEY)).toBeNull();
  expect(fetcher).toHaveBeenCalledTimes(1);
});

it.each(["vendor", "admin"])(
  "chuyển tài khoản %s đến trang theo vai trò",
  async (role) => {
    fetcher.mockResolvedValue(json({ ...result, user: { ...user, role } }));
    const browser = userEvent.setup();
    open("/login");
    await screen.findByLabelText("Email");
    await browser.type(screen.getByLabelText("Email"), user.email);
    await browser.type(screen.getByLabelText("Mật khẩu"), "password123");
    await browser.click(screen.getByRole("button", { name: "Đăng nhập" }));
    await screen.findByRole("heading", { name: "Chào Nguyễn Văn A." });
    expect(
      screen.getAllByText(role === "vendor" ? "Chủ quán" : "Quản trị viên")
        .length,
    ).toBeGreaterThan(0);
  },
);

it("tải lại phiên bằng /me và không tin role giả trong localStorage", async () => {
  localStorage.setItem(
    AUTH_STORAGE_KEY,
    JSON.stringify({ ...tokens, user: { ...user, role: "admin" } }),
  );
  apiClient.syncFromStorage();
  fetcher.mockResolvedValue(json(user));
  open("/admin");
  await screen.findByRole("heading", {
    name: "Trang này dành cho vai trò khác.",
  });
  expect(fetcher.mock.calls[0][0]).toBe("/api/v1/auth/me");
  expect(
    screen.queryByRole("heading", { name: "Chào Nguyễn Văn A." }),
  ).toBeNull();
});

it("giữ phiên khi mất mạng và cho phép thử lại", async () => {
  savedSession();
  fetcher
    .mockRejectedValueOnce(new TypeError("offline"))
    .mockResolvedValue(json(user));
  const browser = userEvent.setup();
  open("/account");
  await screen.findByRole("heading", { name: "Chưa kết nối được tài khoản" });
  expect(localStorage.getItem(AUTH_STORAGE_KEY)).not.toBeNull();
  await browser.click(screen.getByRole("button", { name: "Thử lại" }));
  await screen.findByRole("heading", { name: "Chào Nguyễn Văn A." });
});

it("refresh bị từ chối đưa người dùng về đăng nhập", async () => {
  savedSession();
  fetcher.mockImplementation(async () =>
    json({ error: { code: "UNAUTHENTICATED", message: "Hết phiên" } }, 401),
  );
  open("/account");
  await screen.findByRole("heading", { name: "Chào mừng bạn trở lại" });
  expect(fetcher).toHaveBeenCalledTimes(2);
  expect(localStorage.getItem(AUTH_STORAGE_KEY)).toBeNull();
});

it("đồng bộ logout từ tab khác và chặn trang riêng", async () => {
  savedSession();
  fetcher.mockResolvedValue(json(user));
  open("/account");
  await screen.findByRole("heading", { name: "Chào Nguyễn Văn A." });
  localStorage.removeItem(AUTH_STORAGE_KEY);
  window.dispatchEvent(
    new StorageEvent("storage", { key: AUTH_STORAGE_KEY, newValue: null }),
  );
  await screen.findByRole("heading", { name: "Chào mừng bạn trở lại" });
});

it("đăng ký chỉ có customer/vendor, kiểm tra xác nhận mật khẩu và chuyển về đăng nhập", async () => {
  fetcher.mockResolvedValue(json({ ...user, role: "vendor" }, 201));
  const browser = userEvent.setup();
  open("/register");
  await screen.findByLabelText("Họ và tên");
  expect(
    screen.getAllByRole("option").map((option) => option.textContent),
  ).toEqual(["Khách hàng", "Chủ quán"]);
  await browser.type(screen.getByLabelText("Họ và tên"), user.full_name);
  await browser.type(screen.getByLabelText("Email"), user.email);
  await browser.type(
    screen.getByLabelText("Mật khẩu", { exact: true }),
    "password123",
  );
  await browser.type(
    screen.getByLabelText("Xác nhận mật khẩu"),
    "different123",
  );
  await browser.click(screen.getByRole("checkbox", { name: /Tôi đồng ý/ }));
  await browser.click(screen.getByRole("button", { name: "Tạo tài khoản" }));
  expect((await screen.findByRole("alert")).textContent).toBe(
    "Mật khẩu xác nhận chưa khớp.",
  );
  expect(fetcher).not.toHaveBeenCalled();
  await browser.clear(screen.getByLabelText("Xác nhận mật khẩu"));
  await browser.type(screen.getByLabelText("Xác nhận mật khẩu"), "password123");
  await browser.selectOptions(
    screen.getByLabelText("Loại tài khoản"),
    "vendor",
  );
  await browser.click(screen.getByRole("button", { name: "Tạo tài khoản" }));
  await screen.findByRole("heading", { name: "Chào mừng bạn trở lại" });
  expect(screen.getByRole("status").textContent).toContain("Đã tạo tài khoản");
  expect((screen.getByLabelText("Email") as HTMLInputElement).value).toBe(
    user.email,
  );
  expect((screen.getByLabelText("Mật khẩu") as HTMLInputElement).value).toBe(
    "",
  );
  expect(JSON.parse(fetcher.mock.calls[0][1]!.body as string)).toEqual({
    email: user.email,
    password: "password123",
    full_name: user.full_name,
    role: "vendor",
  });
  expect(localStorage.getItem(AUTH_STORAGE_KEY)).toBeNull();
});

it.each([
  [401, "Email hoặc mật khẩu không đúng."],
  [409, "Email đã được sử dụng."],
  [503, "Cần cấu hình SECRET_KEY trước khi sử dụng JWT."],
])("hiển thị thông báo API %s trên form đăng nhập", async (status, message) => {
  fetcher.mockResolvedValue(
    json({ error: { code: "ERROR", message } }, status as number),
  );
  const browser = userEvent.setup();
  open("/login");
  await screen.findByLabelText("Email");
  await browser.type(screen.getByLabelText("Email"), user.email);
  await browser.type(screen.getByLabelText("Mật khẩu"), "password123");
  await browser.click(screen.getByRole("button", { name: "Đăng nhập" }));
  expect((await screen.findByRole("alert")).textContent).toBe(message);
  expect(localStorage.getItem(AUTH_STORAGE_KEY)).toBeNull();
});

it("khóa nút gửi trong khi đăng nhập để tránh gửi lặp", async () => {
  let resolve!: (response: Response) => void;
  fetcher.mockReturnValue(
    new Promise<Response>((done) => {
      resolve = done;
    }),
  );
  const browser = userEvent.setup();
  open("/login");
  await screen.findByLabelText("Email");
  await browser.type(screen.getByLabelText("Email"), user.email);
  await browser.type(screen.getByLabelText("Mật khẩu"), "password123");
  await browser.click(screen.getByRole("button", { name: "Đăng nhập" }));
  const pending = screen.getByRole("button", {
    name: "Đang đăng nhập…",
  }) as HTMLButtonElement;
  expect(pending.matches(":disabled")).toBe(true);
  await browser.click(pending);
  expect(fetcher).toHaveBeenCalledTimes(1);
  resolve(json(result));
  await screen.findByRole("heading", { name: "Chào Nguyễn Văn A." });
});

it("có trang 404 và điều hướng về trang chủ", async () => {
  const browser = userEvent.setup();
  open("/missing");
  expect(
    screen.getByRole("heading", { name: "Chưa tìm thấy trang bạn cần." }),
  ).toBeTruthy();
  await browser.click(screen.getByRole("link", { name: "Về trang chủ" }));
  await waitFor(() =>
    expect(screen.getByRole("heading", { name: /Hẹn bạn/ })).toBeTruthy(),
  );
});

it("báo lỗi ngay dưới trường và đưa focus về trường đầu tiên chưa hợp lệ", async () => {
  const browser = userEvent.setup();
  open("/login");
  const email = await screen.findByLabelText("Email");
  await browser.click(screen.getByRole("button", { name: "Đăng nhập" }));
  expect(document.activeElement).toBe(email);
  expect(email.getAttribute("aria-invalid")).toBe("true");
  expect(screen.getByText("Vui lòng nhập email.")).toBeTruthy();
  expect(screen.getByText("Vui lòng nhập mật khẩu.")).toBeTruthy();
  await browser.type(email, "sai-email");
  await browser.tab();
  expect(screen.getByText(/Email chưa đúng định dạng/)).toBeTruthy();
  expect(fetcher).not.toHaveBeenCalled();
});

it("hiện/ẩn mật khẩu mà không gửi form hoặc làm mất dữ liệu", async () => {
  const browser = userEvent.setup();
  open("/login");
  const password = (await screen.findByLabelText(
    "Mật khẩu",
  )) as HTMLInputElement;
  await browser.type(password, "  Mat khau  ");
  await browser.click(screen.getByRole("button", { name: "Hiện mật khẩu" }));
  expect(password.type).toBe("text");
  expect(password.value).toBe("  Mat khau  ");
  await browser.click(screen.getByRole("button", { name: "Ẩn mật khẩu" }));
  expect(password.type).toBe("password");
  expect(fetcher).not.toHaveBeenCalled();
});

it("bỏ ghi nhớ đăng nhập lưu token ở sessionStorage thay vì localStorage", async () => {
  fetcher.mockResolvedValue(json(result));
  const browser = userEvent.setup();
  open("/login");
  await browser.type(await screen.findByLabelText("Email"), user.email);
  await browser.type(screen.getByLabelText("Mật khẩu"), "password123");
  await browser.click(
    screen.getByRole("checkbox", { name: "Ghi nhớ đăng nhập" }),
  );
  await browser.click(screen.getByRole("button", { name: "Đăng nhập" }));
  await screen.findByRole("heading", { name: "Chào Nguyễn Văn A." });
  expect(localStorage.getItem(AUTH_STORAGE_KEY)).toBeNull();
  expect(JSON.parse(sessionStorage.getItem(AUTH_STORAGE_KEY)!)).toEqual(tokens);
});

it("quên mật khẩu mở hướng dẫn thật, không gọi API đặt lại mật khẩu giả", async () => {
  const browser = userEvent.setup();
  open("/login");
  await browser.click(
    await screen.findByRole("button", { name: "Quên mật khẩu?" }),
  );
  expect(screen.getByRole("dialog", { name: "Hỗ trợ đăng nhập" })).toBeTruthy();
  expect(
    screen.getByText("Vị Việt hiện chưa hỗ trợ đặt lại mật khẩu qua email."),
  ).toBeTruthy();
  await browser.click(screen.getByRole("button", { name: "Đã hiểu" }));
  expect(screen.queryByRole("dialog")).toBeNull();
  expect(fetcher).not.toHaveBeenCalled();
});

it("điều khoản và chính sách có nội dung, không tự đánh dấu đồng ý", async () => {
  const browser = userEvent.setup();
  open("/register");
  await screen.findByLabelText("Họ và tên");
  await browser.click(
    screen.getAllByRole("button", {
      name: "Điều khoản sử dụng",
    })[0],
  );
  expect(
    screen.getByRole("dialog", { name: "Điều khoản sử dụng" }),
  ).toBeTruthy();
  await browser.click(screen.getByRole("button", { name: "Đã hiểu" }));
  await browser.click(
    screen.getAllByRole("button", {
      name: "Chính sách bảo mật",
    })[0],
  );
  expect(
    screen.getByRole("dialog", { name: "Chính sách bảo mật" }),
  ).toBeTruthy();
  await browser.click(screen.getByRole("button", { name: "Đóng hộp thoại" }));
  expect(
    (screen.getByRole("checkbox", { name: /Tôi đồng ý/ }) as HTMLInputElement)
      .checked,
  ).toBe(false);
});

it("đăng ký yêu cầu đồng ý, giữ dữ liệu và hiển thị email trùng tại đúng trường", async () => {
  fetcher.mockResolvedValue(
    json(
      { error: { code: "EMAIL_EXISTS", message: "Email đã được sử dụng." } },
      409,
    ),
  );
  const browser = userEvent.setup();
  open("/register");
  await browser.type(await screen.findByLabelText("Họ và tên"), user.full_name);
  await browser.type(screen.getByLabelText("Email"), user.email);
  await browser.type(
    screen.getByLabelText("Mật khẩu", { exact: true }),
    "password123",
  );
  await browser.type(screen.getByLabelText("Xác nhận mật khẩu"), "password123");
  await browser.click(screen.getByRole("button", { name: "Tạo tài khoản" }));
  expect(screen.getByText(/Bạn cần đồng ý với điều khoản/)).toBeTruthy();
  expect(fetcher).not.toHaveBeenCalled();
  await browser.click(screen.getByRole("checkbox", { name: /Tôi đồng ý/ }));
  await browser.click(screen.getByRole("button", { name: "Tạo tài khoản" }));
  await screen.findByText(/Email đã được sử dụng. Bạn có thể đăng nhập/);
  expect(screen.getByLabelText("Email").getAttribute("aria-invalid")).toBe(
    "true",
  );
  expect(document.activeElement).toBe(screen.getByLabelText("Email"));
  expect(
    (screen.getByLabelText("Mật khẩu", { exact: true }) as HTMLInputElement)
      .value,
  ).toBe("password123");
  expect(
    JSON.parse(fetcher.mock.calls[0][1]!.body as string),
  ).not.toHaveProperty("consent");
});

it("dịch lỗi validation của API sang tiếng Việt tại trường tương ứng", async () => {
  fetcher.mockResolvedValue(
    json(
      {
        error: {
          code: "VALIDATION_ERROR",
          message: "Dữ liệu không hợp lệ.",
          details: [
            {
              field: ["body", "email"],
              message: "String should match pattern",
              type: "string_pattern_mismatch",
            },
          ],
        },
      },
      422,
    ),
  );
  const browser = userEvent.setup();
  open("/login");
  await browser.type(await screen.findByLabelText("Email"), user.email);
  await browser.type(screen.getByLabelText("Mật khẩu"), "password123");
  await browser.click(screen.getByRole("button", { name: "Đăng nhập" }));
  await screen.findByText("Vui lòng kiểm tra lại địa chỉ email.");
  expect(screen.queryByText("String should match pattern")).toBeNull();
  expect(document.activeElement).toBe(screen.getByLabelText("Email"));
});

it("lỗi cấu hình máy chủ hiển thị thông báo có ích cho người đăng nhập", async () => {
  fetcher.mockResolvedValue(
    json(
      {
        error: {
          code: "AUTH_NOT_CONFIGURED",
          message: "Cần cấu hình SECRET_KEY trước khi sử dụng JWT.",
        },
      },
      503,
    ),
  );
  const browser = userEvent.setup();
  open("/login");
  await browser.type(await screen.findByLabelText("Email"), user.email);
  await browser.type(screen.getByLabelText("Mật khẩu"), "password123");
  await browser.click(screen.getByRole("button", { name: "Đăng nhập" }));
  await screen.findByText(
    "Dịch vụ đăng nhập chưa sẵn sàng. Vui lòng thử lại sau.",
  );
  expect(screen.queryByText(/SECRET_KEY/)).toBeNull();
});
