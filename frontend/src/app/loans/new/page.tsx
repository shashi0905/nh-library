/** Borrow form page with member/book selector and due date. */

"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { loansApi, booksApi, membersApi, BookResponse, MemberResponse, LoanCreate } from "@/lib/api";
import { FormField } from "@/components/FormField";

export default function BorrowBookPage() {
  const router = useRouter();
  const [books, setBooks] = useState<BookResponse[]>([]);
  const [members, setMembers] = useState<MemberResponse[]>([]);
  const [formData, setFormData] = useState<LoanCreate>({
    book_id: "",
    member_id: "",
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchBooks = async () => {
    try {
      const response = await booksApi.list({ limit: 100 });
      setBooks(response.items.filter((book) => book.available > 0));
    } catch (err) {
      console.error("Failed to fetch books:", err);
    }
  };

  const fetchMembers = async () => {
    try {
      const response = await membersApi.list({ limit: 100 });
      setMembers(response.items.filter((member) => member.is_active));
    } catch (err) {
      console.error("Failed to fetch members:", err);
    }
  };

  useEffect(() => {
    Promise.all([fetchBooks(), fetchMembers()]).finally(() => {
      setIsLoading(false);
    });
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      await loansApi.create(formData);
      router.push("/loans");
    } catch (err) {
      const apiError = err as { message?: string };
      setError(apiError.message || "Failed to create loan");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value,
    });
  };

  if (isLoading) {
    return <div className="text-center py-8">Loading...</div>;
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Borrow Book</h1>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6">
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="member_id" className="block text-sm font-medium text-gray-700 mb-1">
              Member
            </label>
            <select
              id="member_id"
              name="member_id"
              value={formData.member_id}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select a member</option>
              {members.map((member) => (
                <option key={member.id} value={member.id}>
                  {member.name} ({member.email})
                </option>
              ))}
            </select>
          </div>

          <div className="mb-4">
            <label htmlFor="book_id" className="block text-sm font-medium text-gray-700 mb-1">
              Book
            </label>
            <select
              id="book_id"
              name="book_id"
              value={formData.book_id}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select a book</option>
              {books.map((book) => (
                <option key={book.id} value={book.id}>
                  {book.title} by {book.author} ({book.available} available)
                </option>
              ))}
            </select>
          </div>

          {error && (
            <div
              className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700"
              role="alert"
            >
              {error}
            </div>
          )}

          <div className="flex space-x-3">
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {isSubmitting ? "Creating..." : "Create Loan"}
            </button>
            <button
              type="button"
              onClick={() => router.push("/loans")}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
