/** Dashboard page with stats cards (total books, active loans, overdue count). */

"use client";

import { useState, useEffect } from "react";
import { booksApi, membersApi, loansApi } from "@/lib/api";
import type { BookListResponse, MemberListResponse, LoanListResponse } from "@/lib/api";

export default function DashboardPage() {
  const [stats, setStats] = useState({
    totalBooks: 0,
    totalMembers: 0,
    activeLoans: 0,
    overdueLoans: 0,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = async () => {
    setIsLoading(true);
    setError(null);
    try {
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const [_, membersResponse, __]: [
        BookListResponse,
        MemberListResponse,
        LoanListResponse,
      ] = await Promise.all([
        booksApi.list({ limit: 1 }),
        membersApi.list({ limit: 1 }),
        loansApi.list({ limit: 1 }),
      ]);

      // Fetch full counts by making additional calls
      const [allBooks, allLoans]: [BookListResponse, LoanListResponse] =
        await Promise.all([
          booksApi.list({ limit: 1000 }),
          loansApi.list({ limit: 1000 }),
        ]);

      const activeLoans = allLoans.items.filter(
        (loan) => loan.status === "ACTIVE" || loan.status === "OVERDUE",
      ).length;
      const overdueLoans = allLoans.items.filter(
        (loan) => loan.status === "OVERDUE",
      ).length;

      setStats({
        totalBooks: allBooks.items.length,
        totalMembers: membersResponse.items.length,
        activeLoans,
        overdueLoans,
      });
    } catch (err) {
      const apiError = err as { message?: string };
      setError(apiError.message || "Failed to fetch dashboard stats");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  if (isLoading) {
    return <div className="text-center py-8">Loading dashboard...</div>;
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

      {error && (
        <div
          className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700"
          role="alert"
        >
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-500">Total Books</p>
              <p className="text-3xl font-bold text-gray-900">{stats.totalBooks}</p>
            </div>
            <div className="p-3 bg-blue-100 rounded-full">
              <svg
                className="w-6 h-6 text-blue-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                />
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-500">Total Members</p>
              <p className="text-3xl font-bold text-gray-900">{stats.totalMembers}</p>
            </div>
            <div className="p-3 bg-green-100 rounded-full">
              <svg
                className="w-6 h-6 text-green-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                />
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-500">Active Loans</p>
              <p className="text-3xl font-bold text-gray-900">{stats.activeLoans}</p>
            </div>
            <div className="p-3 bg-yellow-100 rounded-full">
              <svg
                className="w-6 h-6 text-yellow-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-500">Overdue Loans</p>
              <p className="text-3xl font-bold text-red-600">{stats.overdueLoans}</p>
            </div>
            <div className="p-3 bg-red-100 rounded-full">
              <svg
                className="w-6 h-6 text-red-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
