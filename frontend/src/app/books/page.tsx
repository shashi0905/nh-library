/** Books list page with searchable table, pagination, and Add Book button. */

"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { booksApi } from "@/lib/api";
import type { BookResponse, BookListResponse } from "@/lib/api";
import { DataTable } from "@/components/DataTable";
import type { Column } from "@/components/DataTable";

const columns: Column<BookResponse>[] = [
  { key: "isbn", label: "ISBN", sortable: true },
  { key: "title", label: "Title", sortable: true },
  { key: "author", label: "Author", sortable: true },
  { key: "total_copies", label: "Total Copies", sortable: true },
  { key: "available", label: "Available", sortable: true },
];

export default function BooksPage() {
  const router = useRouter();
  const [books, setBooks] = useState<BookResponse[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchBooks = async (cursor?: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const response: BookListResponse = await booksApi.list({
        q: searchQuery || undefined,
        cursor,
        limit: 20,
      });
      if (cursor) {
        setBooks((prev) => [...prev, ...response.items]);
      } else {
        setBooks(response.items);
      }
      setNextCursor(response.next_cursor);
    } catch (err) {
      const apiError = err as { message?: string };
      setError(apiError.message || "Failed to fetch books");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchBooks();
  }, [searchQuery]);

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
    setNextCursor(null);
  };

  const handleLoadMore = () => {
    if (nextCursor) {
      fetchBooks(nextCursor);
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Books</h1>
        <button
          type="button"
          onClick={() => router.push("/books/new")}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Add Book
        </button>
      </div>

      <div className="mb-4">
        <input
          type="text"
          value={searchQuery}
          onChange={handleSearch}
          placeholder="Search books by title, author, or ISBN..."
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          aria-label="Search books"
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
        data={books}
        onNextPage={handleLoadMore}
        hasNextPage={!!nextCursor}
        isLoading={isLoading}
      />
    </div>
  );
}
