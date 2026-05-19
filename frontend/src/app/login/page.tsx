/** Login page with email/password form and httpOnly cookie auth. */

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { authApi, TokenRequest } from "@/lib/api";
import { FormField } from "@/components/FormField";

export default function LoginPage() {
  const router = useRouter();
  const [formData, setFormData] = useState<TokenRequest>({
    email: "",
    password: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      await authApi.login(formData);
      router.push("/");
    } catch (err) {
      const apiError = err as { message?: string; detail?: unknown };
      setError(
        apiError.message || "Login failed. Please check your credentials.",
      );
      setIsLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8">
        <h1 className="text-2xl font-bold text-center text-gray-900 mb-8">
          Neighborhood Library
        </h1>
        <h2 className="text-xl font-semibold text-center text-gray-700 mb-6">
          Staff Login
        </h2>
        <form onSubmit={handleSubmit}>
          <FormField
            id="email"
            name="email"
            label="Email"
            type="email"
            value={formData.email}
            onChange={handleChange}
            required
            autoComplete="email"
            placeholder="staff@example.com"
          />
          <FormField
            id="password"
            name="password"
            label="Password"
            type="password"
            value={formData.password}
            onChange={handleChange}
            required
            autoComplete="current-password"
            placeholder="••••••••"
          />
          {error && (
            <div
              className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700"
              role="alert"
            >
              {error}
            </div>
          )}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {isLoading ? "Logging in..." : "Login"}
          </button>
        </form>
      </div>
    </div>
  );
}
