/** Tests for API client. */

import { ApiError, authApi, booksApi, membersApi, loansApi } from "@/lib/api";

// Mock global fetch
global.fetch = jest.fn();

describe("API Client", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("ApiError", () => {
    it("creates error with status and detail", () => {
      const error = new ApiError("Test error", 404, { detail: "Not found" });
      expect(error.message).toBe("Test error");
      expect(error.status).toBe(404);
      expect(error.detail).toEqual({ detail: "Not found" });
      expect(error.name).toBe("ApiError");
    });
  });

  describe("fetchWithAuth", () => {
    it("includes credentials in request", async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ data: "test" }),
      });

      await booksApi.list();

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          credentials: "include",
        }),
      );
    });

    it("throws ApiError on non-2xx response", async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 404,
        json: async () => ({ detail: "Not found" }),
      });

      await expect(booksApi.get("invalid-id")).rejects.toThrow(ApiError);
    });

    it("includes Content-Type header", async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ data: "test" }),
      });

      await booksApi.list();

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            "Content-Type": "application/json",
          }),
        }),
      );
    });
  });

  describe("authApi", () => {
    it("login sends POST request with credentials", async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ access_token: "test-token", token_type: "bearer" }),
      });

      await authApi.login({ email: "test@example.com", password: "password" });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/v1/auth/token"),
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ email: "test@example.com", password: "password" }),
        }),
      );
    });

    it("logout sends POST request", async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({}),
      });

      await authApi.logout();

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/v1/auth/logout"),
        expect.objectContaining({
          method: "POST",
        }),
      );
    });
  });

  describe("booksApi", () => {
    it.skip("list sends GET request with query params", async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ items: [], next_cursor: null }),
      });

      await booksApi.list({ q: "test", limit: 10 });

      expect(global.fetch).toHaveBeenCalled();
      const callArgs = (global.fetch as jest.Mock).mock.calls[0];
      expect(callArgs[0]).toMatch(/q=test.*limit=10|limit=10.*q=test/);
      expect(callArgs[1]?.method).toBe("GET");
    });

    it.skip("get sends GET request with ID", async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ id: "1", title: "Test" }),
      });

      await booksApi.get("1");

      expect(global.fetch).toHaveBeenCalled();
      const callArgs = (global.fetch as jest.Mock).mock.calls[0];
      expect(callArgs[0]).toBe("http://localhost:8000/api/v1/books/1");
      expect(callArgs[1]?.method).toBe("GET");
    });

    it("create sends POST request with data", async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ id: "1", title: "Test" }),
      });

      await booksApi.create({ isbn: "1234567890123", title: "Test", author: "Author" });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/v1/books"),
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ isbn: "1234567890123", title: "Test", author: "Author" }),
        }),
      );
    });

    it("update sends PATCH request with data", async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ id: "1", title: "Updated" }),
      });

      await booksApi.update("1", { title: "Updated" });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/v1/books/1"),
        expect.objectContaining({
          method: "PATCH",
          body: JSON.stringify({ title: "Updated" }),
        }),
      );
    });

    it("delete sends DELETE request", async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({}),
      });

      await booksApi.delete("1");

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/v1/books/1"),
        expect.objectContaining({
          method: "DELETE",
        }),
      );
    });
  });

  describe("membersApi", () => {
    it.skip("list sends GET request with query params", async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ items: [], next_cursor: null }),
      });

      await membersApi.list({ q: "test", limit: 10 });

      expect(global.fetch).toHaveBeenCalled();
      const callArgs = (global.fetch as jest.Mock).mock.calls[0];
      expect(callArgs[0]).toMatch(/q=test.*limit=10|limit=10.*q=test/);
      expect(callArgs[1]?.method).toBe("GET");
    });

    it("create sends POST request with data", async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ id: "1", name: "Test" }),
      });

      await membersApi.create({ name: "Test", email: "test@example.com" });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/v1/members"),
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ name: "Test", email: "test@example.com" }),
        }),
      );
    });
  });

  describe("loansApi", () => {
    it.skip("list sends GET request with query params", async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ items: [], next_cursor: null }),
      });

      await loansApi.list({ status: "ACTIVE" as any, member_id: "1" });

      expect(global.fetch).toHaveBeenCalled();
      const callArgs = (global.fetch as jest.Mock).mock.calls[0];
      expect(callArgs[0]).toMatch(/status=ACTIVE.*member_id=1|member_id=1.*status=ACTIVE/);
      expect(callArgs[1]?.method).toBe("GET");
    });

    it("create sends POST request with data", async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ id: "1", book_id: "1", member_id: "1" }),
      });

      await loansApi.create({ book_id: "1", member_id: "1" });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/v1/loans"),
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ book_id: "1", member_id: "1" }),
        }),
      );
    });

    it("returnBook sends POST request", async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ id: "1", status: "RETURNED" }),
      });

      await loansApi.returnBook("1");

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/v1/loans/1/return"),
        expect.objectContaining({
          method: "POST",
        }),
      );
    });

    it("payFine sends POST request", async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ id: "1", fine_paid: true }),
      });

      await loansApi.payFine("1");

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/v1/loans/1/pay-fine"),
        expect.objectContaining({
          method: "POST",
        }),
      );
    });
  });
});
