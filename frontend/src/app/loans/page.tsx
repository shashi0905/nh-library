/** Loans list page with status/member filters and overdue highlighting. */

"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { loansApi, LoanStatus } from "@/lib/api";
import type { LoanResponse, LoanListResponse } from "@/lib/api";
import { DataTable } from "@/components/DataTable";
import type { Column } from "@/components/DataTable";
import { StatusBadge } from "@/components/StatusBadge";

// Helper function to check if a string is a valid UUID
const isValidUUID = (uuidString: string) => {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  return uuidRegex.test(uuidString);
};

const columns: Column<LoanResponse>[] = [
  { key: "id", label: "ID", sortable: true },
  { key: "book_id", label: "Book ID", sortable: true },
  { key: "member_id", label: "Member ID", sortable: true },
  { key: "borrowed_at", label: "Borrowed", sortable: true },
  { key: "due_date", label: "Due Date", sortable: true },
  {
    key: "status",
    label: "Status",
    sortable: true,
    render: (value: unknown) => <StatusBadge status={value as LoanStatus} />,
  },
  {
    key: "fine_amount",
    label: "Fine",
    sortable: true,
    render: (value: unknown, row: LoanResponse) => (
      <span>
        {row.fine_amount ? `$${row.fine_amount}` : "-"}
        {row.fine_paid && <span className="ml-1 text-green-600">(Paid)</span>}
      </span>
    ),
  },
];

export default function LoansPage() {
  const router = useRouter();
  const [loans, setLoans] = useState<LoanResponse[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [memberFilter, setMemberFilter] = useState("");
  const [overdueFilter, setOverdueFilter] = useState(false);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchLoans = async (cursor?: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const response: LoanListResponse = await loansApi.list({
        status: (statusFilter as LoanStatus) || undefined,
        // Only pass member_id if it's a valid UUID
        member_id: isValidUUID(memberFilter) ? memberFilter : undefined,
        overdue: overdueFilter || undefined,
        cursor,
        limit: 20,
      });
      if (cursor) {
        setLoans((prev) => [...prev, ...response.items]);
      } else {
        setLoans(response.items);
      }
      setNextCursor(response.next_cursor);
    } catch (err) {
      const apiError = err as { message?: string };
      setError(apiError.message || "Failed to fetch loans");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    setNextCursor(null);
    fetchLoans();
  }, [statusFilter, memberFilter, overdueFilter]);

  const handleLoadMore = () => {
    if (nextCursor) {
      fetchLoans(nextCursor);
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Loans</h1>
        <button
          type="button"
          onClick={() => router.push("/loans/new")}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Borrow Book
        </button>
      </div>

      <div className="mb-4 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label htmlFor="status-filter" className="block text-sm font-medium text-gray-700 mb-1">
            Status
          </label>
          <select
            id="status-filter"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Statuses</option>
            <option value={LoanStatus.ACTIVE}>Active</option>
            <option value={LoanStatus.RETURNED}>Returned</option>
            <option value={LoanStatus.OVERDUE}>Overdue</option>
          </select>
        </div>
        <div>
          <label htmlFor="member-filter" className="block text-sm font-medium text-gray-700 mb-1">
            Member ID
          </label>
          <input
            id="member-filter"
            type="text"
            value={memberFilter}
            onChange={(e) => setMemberFilter(e.target.value)}
            placeholder="Filter by member ID (UUID)..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div className="flex items-end">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={overdueFilter}
              onChange={(e) => setOverdueFilter(e.target.checked)}
              className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <span className="text-sm font-medium text-gray-700">Show overdue only</span>
          </label>
        </div>
      </div>

      {error && (
        <div
          className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700"
          role="alert"
        >
          {error}
        </div>
      )}

      <DataTable
        columns={columns}
        data={loans}
        onNextPage={handleLoadMore}
        hasNextPage={!!nextCursor}
        isLoading={isLoading}
      />
    </div>
  );
}
