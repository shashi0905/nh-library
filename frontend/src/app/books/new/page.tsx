"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { booksApi } from "@/lib/api"; // Assuming booksApi has a create method

export default function AddBookPage() {
  const router = useRouter();
  const [isbn, setIsbn] = useState("");
  const [title, setTitle] = useState("");
  const [author, setAuthor] = useState("");
  const [totalCopies, setTotalCopies] = useState<number | string>("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      await booksApi.create({
        isbn,
        title,
        author,
        total_copies: typeof totalCopies === 'number' ? totalCopies : undefined,
      });
      setSuccess("Book added successfully!");
      setIsbn("");
      setTitle("");
      setAuthor("");
      setTotalCopies("");
      // Optionally, redirect to the books list after successful addition
      router.push("/books");
    } catch (err) {
      const apiError = err as { message?: string; detail?: unknown };
      const errorMessage = typeof apiError.detail === "string" 
        ? apiError.detail 
        : apiError.message || "Failed to add book.";
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-10 p-6 bg-white rounded-lg shadow-md">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Add New Book</h1>

      {error && (
        <div
          className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700"
          role="alert"
        >
          {error}
        </div>
      )}
      {success && (
        <div
          className="mb-4 p-3 bg-green-50 border border-green-200 rounded-md text-sm text-green-700"
          role="alert"
        >
          {success}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label htmlFor="isbn" className="block text-sm font-medium text-gray-700">
            ISBN
          </label>
          <input
            type="text"
            id="isbn"
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            value={isbn}
            onChange={(e) => setIsbn(e.target.value)}
            required
          />
        </div>
        <div className="mb-4">
          <label htmlFor="title" className="block text-sm font-medium text-gray-700">
            Title
          </label>
          <input
            type="text"
            id="title"
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
          />
        </div>
        <div className="mb-4">
          <label htmlFor="author" className="block text-sm font-medium text-gray-700">
            Author
          </label>
          <input
            type="text"
            id="author"
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            value={author}
            onChange={(e) => setAuthor(e.target.value)}
            required
          />
        </div>
        <div className="mb-6">
          <label htmlFor="totalCopies" className="block text-sm font-medium text-gray-700">
            Total Copies (Optional)
          </label>
          <input
            type="number"
            id="totalCopies"
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            value={totalCopies}
            onChange={(e) => setTotalCopies(e.target.value === '' ? '' : Number(e.target.value))}
            min="1"
          />
        </div>
        <button
          type="submit"
          className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          disabled={isLoading}
        >
          {isLoading ? "Adding Book..." : "Add Book"}
        </button>
      </form>
    </div>
  );
}