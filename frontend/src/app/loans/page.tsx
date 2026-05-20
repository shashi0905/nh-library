/** Loans list page with status/member filters and overdue highlighting. */

"use client";

import { useState, useEffect, useMemo } from "react"; // Import useMemo
import { useRouter } from "next/navigation";
import {
  loansApi,
  booksApi, // Import booksApi
  membersApi, // Import membersApi
  LoanResponse,
  LoanListResponse,
  LoanStatus,
  BookResponse, // Import BookResponse
  MemberResponse, // Import MemberResponse
} from "@/lib/api";
import { DataTable } from "@/components/DataTable";
import type { Column } from "@/components/DataTable";
import { StatusBadge } from "@/components/StatusBadge";

// Helper function to check if a string is a valid UUID
const isValidUUID = (uuidString: string) => {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  return uuidRegex.test(uuidString);
};

export default function LoansPage() {
  const router = useRouter();
  const [loans, setLoans] = useState<LoanResponse[]>([]);
  const [allBooks, setAllBooks] = useState<BookResponse[]>([]); // State for all books
  const [allMembers, setAllMembers] = useState<MemberResponse[]>([]); // State for all members
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [memberFilter, setMemberFilter] = useState("");
  const [overdueFilter, setOverdueFilter] = useState(false);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true); // Set to true initially to load books/members
  const [error, setError] = useState<string | null>(null);

  const fetchLoans = async (cursor?: string) => {
    // Only set loading for loans if initial data (books/members) is already loaded
    if (allBooks.length > 0 || allMembers.length > 0) {
      setIsLoading(true);
    }
    setError(null); // Clear previous errors
    try {
      const response: LoanListResponse = await loansApi.list({
        status: (statusFilter as LoanStatus) || undefined,
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
      // Only set loading for loans if initial data (books/members) is already loaded
      if (allBooks.length > 0 || allMembers.length > 0) {
        setIsLoading(false);
      }
    }
  };

  const fetchAllInitialData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [booksResponse, membersResponse] = await Promise.all([
        booksApi.list({ limit: 1000 }), // Fetch all books (adjust limit as needed)
        membersApi.list({ limit: 1000 }), // Fetch all members (adjust limit as needed)
      ]);
      setAllBooks(booksResponse.items);
      setAllMembers(membersResponse.items);
      // After fetching all books and members, then fetch loans
      await fetchLoans();
    } catch (err) {
      console.error("Failed to fetch initial data:", err);
      const apiError = err as { message?: string };
      setError(apiError.message || "Failed to fetch initial data (books/members)");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAllInitialData();
  }, []); // Run once on mount to fetch all books, members, and initial loans

  useEffect(() => {
    // Only refetch loans if initial data (books/members) has been loaded
    if (!isLoading && (allBooks.length > 0 || allMembers.length > 0)) {
      setNextCursor(null);
      fetchLoans();
    }
  }, [statusFilter, memberFilter, overdueFilter, allBooks, allMembers]); // Re-fetch loans when filters change or initial data is ready

  const handleLoadMore = () => {
    if (nextCursor) {
      fetchLoans(nextCursor);
    }
  };

  const handleRowClick = (loan: LoanResponse) => {
    router.push(`/loans/${loan.id}`);
  };

  // Memoize the book and member maps for efficient lookups
  const bookMap = useMemo(() => {
    return new Map(allBooks.map((book) => [book.id, book]));
  }, [allBooks]);

  const memberMap = useMemo(() => {
    return new Map(allMembers.map((member) => [member.id, member]));
  }, [allMembers]);

  // Define columns using the memoized maps
  const columns: Column<LoanResponse>[] = [
    { key: "id", label: "ID", sortable: true },
    {
      key: "book_id",
      label: "Book Title",
      sortable: true,
      render: (value: unknown) => {
        const book = bookMap.get(value as string);
        return book ? book.title : (value as string);
      },
    },
    {
      key: "member_id",
      label: "Member Name",
      sortable: true,
      render: (value: unknown) => {
        const member = memberMap.get(value as string);
        return member ? member.name : (value as string);
      },
    },
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