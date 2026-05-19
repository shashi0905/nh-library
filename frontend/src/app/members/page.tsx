/** Members list page with searchable table and Register Member button. */

"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { membersApi, MemberResponse, MemberListResponse } from "@/lib/api";
import { DataTable, Column } from "@/components/DataTable";

const columns: Column<MemberResponse>[] = [
  { key: "name", label: "Name", sortable: true },
  { key: "email", label: "Email", sortable: true },
  { key: "phone", label: "Phone", sortable: true },
  { key: "joined_at", label: "Joined", sortable: true },
  {
    key: "is_active",
    label: "Status",
    sortable: true,
    render: (value: unknown) => (
      <span
        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
          value ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
        }`}
      >
        {value ? "Active" : "Inactive"}
      </span>
    ),
  },
];

export default function MembersPage() {
  const router = useRouter();
  const [members, setMembers] = useState<MemberResponse[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchMembers = async (cursor?: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const response: MemberListResponse = await membersApi.list({
        q: searchQuery || undefined,
        cursor,
        limit: 20,
      });
      if (cursor) {
        setMembers((prev) => [...prev, ...response.items]);
      } else {
        setMembers(response.items);
      }
      setNextCursor(response.next_cursor);
    } catch (err) {
      const apiError = err as { message?: string };
      setError(apiError.message || "Failed to fetch members");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMembers();
  }, [searchQuery]);

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
    setNextCursor(null);
  };

  const handleLoadMore = () => {
    if (nextCursor) {
      fetchMembers(nextCursor);
    }
  };

  const handleRowClick = (member: MemberResponse) => {
    router.push(`/members/${member.id}`);
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Members</h1>
        <button
          type="button"
          onClick={() => router.push("/members/new")}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Register Member
        </button>
      </div>

      <div className="mb-4">
        <input
          type="text"
          value={searchQuery}
          onChange={handleSearch}
          placeholder="Search members by name or email..."
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          aria-label="Search members"
        />
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
        data={members}
        onNextPage={handleLoadMore}
        hasNextPage={!!nextCursor}
        isLoading={isLoading}
      />
    </div>
  );
}
