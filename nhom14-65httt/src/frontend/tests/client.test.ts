import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  ApiClient,
  ApiError,
  AUTH_STORAGE_KEY,
  SessionChangedError,
} from "../src/api/client";
import { safeReturnTo } from "../src/utils/auth";

const user = {
  id: 1,
  email: "khach@example.vn",
  full_name: "Khách",
  role: "customer",
  is_simulated: false,
  created_at: "2026-11-26T10:00:00Z",
};
const oldTokens = { access_token: "old-access", refresh_token: "old-refresh" };
const newTokens = { access_token: "new-access", refresh_token: "new-refresh" };
const tokenResponse = {
  ...newTokens,
  user,
  token_type: "bearer",
  expires_in: 3600,
};
const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status });
const denied = (status = 401) =>
  json({ error: { code: "UNAUTHENTICATED", message: "Hết phiên." } }, status);
function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => {
    resolve = done;
  });
  return { promise, resolve };
}
function makeClient(fetcher: typeof fetch) {
  return new ApiClient("/api/v1", fetcher, localStorage);
}
beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
  localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(oldTokens));
});
afterEach(() => {
  vi.useRealTimers();
});

describe("API session", () => {
  it("gửi mật khẩu nguyên dạng và chỉ lưu hai token", async () => {
    const fetcher = vi
      .fn<typeof fetch>()
      .mockResolvedValue(json(tokenResponse));
    const client = makeClient(fetcher);
    expect(
      await client.login({ email: user.email, password: "  mật khẩu  " }),
    ).toEqual(user);
    expect(JSON.parse(localStorage.getItem(AUTH_STORAGE_KEY)!)).toEqual(
      newTokens,
    );
    expect(JSON.parse(fetcher.mock.calls[0][1]!.body as string).password).toBe(
      "  mật khẩu  ",
    );
    expect(
      new Headers(fetcher.mock.calls[0][1]!.headers).has("Authorization"),
    ).toBe(false);
    expect(localStorage.getItem(AUTH_STORAGE_KEY)).not.toContain("mật khẩu");
  });

  it.each([
    "bad json",
    "null",
    "[]",
    '{"access_token":"a"}',
    '{"access_token":"a","refresh_token":123}',
  ])("bỏ qua dữ liệu lưu không hợp lệ: %s", (raw) => {
    localStorage.setItem(AUTH_STORAGE_KEY, raw);
    expect(makeClient(vi.fn()).hasSession).toBe(false);
  });

  it("không gắn access token vào yêu cầu công khai", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(json(user));
    await makeClient(fetcher).request("/auth/register", {
      authenticated: false,
      headers: { Authorization: "Bearer injected" },
    });
    expect(
      new Headers(fetcher.mock.calls[0][1]!.headers).has("Authorization"),
    ).toBe(false);
  });

  it("gộp hai yêu cầu hết hạn thành một lần refresh và thử lại bằng token mới", async () => {
    const refresh = deferred<Response>();
    const fetcher = vi
      .fn<typeof fetch>()
      .mockImplementation(async (url, options) => {
        if (String(url).endsWith("/refresh")) return refresh.promise;
        return new Headers(options?.headers).get("Authorization") ===
          "Bearer old-access"
          ? denied()
          : json(user);
      });
    const client = makeClient(fetcher);
    const first = client.request("/auth/me");
    const second = client.request("/auth/me");
    await vi.waitFor(() =>
      expect(
        fetcher.mock.calls.filter(([url]) => String(url).endsWith("/refresh")),
      ).toHaveLength(1),
    );
    refresh.resolve(json(tokenResponse));
    expect(await Promise.all([first, second])).toEqual([user, user]);
    expect(fetcher).toHaveBeenCalledTimes(5);
    const refreshCall = fetcher.mock.calls.find(([url]) =>
      String(url).endsWith("/refresh"),
    )!;
    expect(new Headers(refreshCall[1]?.headers).has("Authorization")).toBe(
      false,
    );
    expect(JSON.parse(refreshCall[1]?.body as string)).toEqual({
      refresh_token: "old-refresh",
    });
  });

  it("không refresh vô hạn nếu API tiếp tục trả 401", async () => {
    const fetcher = vi
      .fn<typeof fetch>()
      .mockImplementation(async (url) =>
        String(url).endsWith("/refresh") ? json(tokenResponse) : denied(),
      );
    const client = makeClient(fetcher);
    await expect(client.request("/auth/me")).rejects.toBeInstanceOf(ApiError);
    expect(fetcher).toHaveBeenCalledTimes(3);
    expect(client.hasSession).toBe(false);
    expect(localStorage.getItem(AUTH_STORAGE_KEY)).toBeNull();
  });

  it.each([401, 422])("xóa phiên khi refresh trả %s", async (status) => {
    const fetcher = vi
      .fn<typeof fetch>()
      .mockImplementation(async (url) =>
        denied(String(url).endsWith("/refresh") ? status : 401),
      );
    const client = makeClient(fetcher);
    await expect(client.request("/auth/me")).rejects.toBeInstanceOf(Error);
    expect(client.hasSession).toBe(false);
  });

  it.each(["network", "server"])(
    "giữ token để thử lại khi refresh lỗi %s",
    async (kind) => {
      const fetcher = vi.fn<typeof fetch>().mockImplementation(async (url) => {
        if (!String(url).endsWith("/refresh")) return denied();
        if (kind === "network") throw new TypeError("offline");
        return denied(503);
      });
      const client = makeClient(fetcher);
      await expect(client.request("/auth/me")).rejects.toBeInstanceOf(Error);
      expect(client.hasSession).toBe(true);
      expect(JSON.parse(localStorage.getItem(AUTH_STORAGE_KEY)!)).toEqual(
        oldTokens,
      );
    },
  );

  it("403 không làm mất phiên hoặc gọi refresh", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(denied(403));
    const client = makeClient(fetcher);
    await expect(client.request("/admin")).rejects.toMatchObject({
      status: 403,
    });
    expect(client.hasSession).toBe(true);
    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it("refresh đang chờ không khôi phục phiên sau khi đăng xuất", async () => {
    const refresh = deferred<Response>();
    const fetcher = vi
      .fn<typeof fetch>()
      .mockImplementation(async (url) =>
        String(url).endsWith("/refresh") ? refresh.promise : denied(),
      );
    const client = makeClient(fetcher);
    const result = client.request("/auth/me").catch((error) => error);
    await vi.waitFor(() => expect(fetcher).toHaveBeenCalledTimes(2));
    client.logout();
    refresh.resolve(json(tokenResponse));
    expect(await result).toBeInstanceOf(SessionChangedError);
    expect(client.hasSession).toBe(false);
    expect(localStorage.getItem(AUTH_STORAGE_KEY)).toBeNull();
  });

  it("đăng nhập đang chờ không khôi phục phiên sau khi đăng xuất", async () => {
    const response = deferred<Response>();
    const client = makeClient(
      vi.fn<typeof fetch>().mockReturnValue(response.promise),
    );
    const result = client
      .login({ email: user.email, password: "secret" })
      .catch((error) => error);
    client.logout();
    response.resolve(json(tokenResponse));
    expect(await result).toBeInstanceOf(SessionChangedError);
    expect(client.hasSession).toBe(false);
  });

  it("phản hồi /me của phiên cũ không ghi đè phiên đăng nhập mới", async () => {
    const oldMe = deferred<Response>();
    const fetcher = vi
      .fn<typeof fetch>()
      .mockImplementation(async (url) =>
        String(url).endsWith("/login") ? json(tokenResponse) : oldMe.promise,
      );
    const client = makeClient(fetcher);
    const result = client.request("/auth/me").catch((error) => error);
    await client.login({ email: user.email, password: "secret" });
    oldMe.resolve(json({ ...user, id: 2 }));
    expect(await result).toBeInstanceOf(SessionChangedError);
    expect(JSON.parse(localStorage.getItem(AUTH_STORAGE_KEY)!)).toEqual(
      newTokens,
    );
  });

  it("không nhận phản hồi token cũ được gửi trong lúc đăng nhập đang chờ", async () => {
    const login = deferred<Response>();
    const oldMe = deferred<Response>();
    const fetcher = vi
      .fn<typeof fetch>()
      .mockImplementation(async (url) =>
        String(url).endsWith("/login") ? login.promise : oldMe.promise,
      );
    const client = makeClient(fetcher);
    const signingIn = client.login({ email: user.email, password: "secret" });
    const result = client.request("/auth/me").catch((error) => error);
    login.resolve(json(tokenResponse));
    await signingIn;
    oldMe.resolve(json({ ...user, id: 2 }));
    expect(await result).toBeInstanceOf(SessionChangedError);
    expect(JSON.parse(localStorage.getItem(AUTH_STORAGE_KEY)!)).toEqual(
      newTokens,
    );
  });

  it("đồng bộ đăng xuất từ tab khác", () => {
    const client = makeClient(vi.fn());
    const listener = vi.fn();
    client.subscribe(listener);
    localStorage.removeItem(AUTH_STORAGE_KEY);
    client.syncFromStorage();
    expect(client.hasSession).toBe(false);
    expect(listener).toHaveBeenCalledWith({ kind: "logout" });
  });

  it("vẫn đăng nhập được trong bộ nhớ khi trình duyệt chặn storage", async () => {
    const storage = {
      getItem: () => null,
      setItem: () => {
        throw new Error("denied");
      },
      removeItem: () => {},
      clear: () => {},
      key: () => null,
      length: 0,
    };
    const client = new ApiClient(
      "/api/v1",
      vi.fn<typeof fetch>().mockResolvedValue(json(tokenResponse)),
      storage,
    );
    await client.login({ email: user.email, password: "secret" });
    expect(client.hasSession).toBe(true);
    expect(client.persisted).toBe(false);
  });

  it("hủy request sau 15 giây", async () => {
    vi.useFakeTimers();
    const fetcher = vi.fn<typeof fetch>().mockImplementation(
      (_url, options) =>
        new Promise((_resolve, reject) => {
          options?.signal?.addEventListener("abort", () =>
            reject(new DOMException("Timeout", "AbortError")),
          );
        }),
    );
    const result = makeClient(fetcher)
      .request("/auth/me")
      .catch((error) => error);
    await vi.advanceTimersByTimeAsync(15_000);
    expect(await result).toMatchObject({ name: "AbortError" });
  });

  it("khôi phục phiên không ghi nhớ từ sessionStorage và logout xóa cả hai nơi", async () => {
    const fetcher = vi
      .fn<typeof fetch>()
      .mockResolvedValue(json(tokenResponse));
    const client = makeClient(fetcher);
    await client.login({ email: user.email, password: "secret" }, false);
    expect(localStorage.getItem(AUTH_STORAGE_KEY)).toBeNull();
    expect(JSON.parse(sessionStorage.getItem(AUTH_STORAGE_KEY)!)).toEqual(
      newTokens,
    );
    expect(makeClient(fetcher).hasSession).toBe(true);
    client.logout();
    expect(sessionStorage.getItem(AUTH_STORAGE_KEY)).toBeNull();
    expect(localStorage.getItem(AUTH_STORAGE_KEY)).toBeNull();
  });

  it("refresh giữ nguyên lựa chọn chỉ lưu theo phiên", async () => {
    const fetcher = vi
      .fn<typeof fetch>()
      .mockImplementation(async (url, options) => {
        if (String(url).endsWith("/login"))
          return json({ ...tokenResponse, ...oldTokens });
        if (String(url).endsWith("/refresh")) return json(tokenResponse);
        return new Headers(options?.headers).get("Authorization") ===
          "Bearer old-access"
          ? denied()
          : json(user);
      });
    const client = makeClient(fetcher);
    await client.login({ email: user.email, password: "secret" }, false);
    await client.request("/auth/me");
    expect(localStorage.getItem(AUTH_STORAGE_KEY)).toBeNull();
    expect(JSON.parse(sessionStorage.getItem(AUTH_STORAGE_KEY)!)).toEqual(
      newTokens,
    );
  });

  it("xóa token cũ khi storage đầy không cho ghi phiên mới", async () => {
    const storage = {
      getItem: () => JSON.stringify(oldTokens),
      setItem: () => {
        throw new Error("quota");
      },
      removeItem: vi.fn(),
      clear: () => {},
      key: () => null,
      length: 1,
    };
    const client = new ApiClient(
      "/api/v1",
      vi.fn<typeof fetch>().mockResolvedValue(json(tokenResponse)),
      storage,
    );
    await client.login({ email: user.email, password: "secret" });
    expect(client.persisted).toBe(false);
    expect(storage.removeItem).toHaveBeenCalledWith(AUTH_STORAGE_KEY);
  });
});

it.each([
  "https://evil.example",
  "//evil.example",
  "/\\evil.example",
  "/%5cevil.example",
  "/login",
  "/register?next=1",
  " /admin",
  null,
])("không điều hướng tới đích không hợp lệ: %s", (path) =>
  expect(safeReturnTo(path, "/account")).toBe("/account"),
);
it("giữ đích nội bộ đã bảo vệ", () =>
  expect(safeReturnTo("/vendor?tab=profile", "/account")).toBe(
    "/vendor?tab=profile",
  ));
