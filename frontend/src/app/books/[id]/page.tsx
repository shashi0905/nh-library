/** Book detail page with edit form, copy count, and loan history. */

"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { booksApi } from "@/lib/api";
import type { BookResponse, BookUpdate } from "@/lib/api";
import { FormField } from "@/components/FormField";
import { ConfirmDialog } from "@/components/ConfirmDialog";

export default function BookDetailPage() {
  const router = useRouter();
  const params = useParams();
  const bookId = params.id as string;

  const [book, setBook] = useState<BookResponse | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [formData, setFormData] = useState<BookUpdate>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchBook = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await booksApi.get(bookId);
      setBook(response);
      setFormData({
        isbn: response.isbn,
        title: response.title,
        author: response.author,
        total_copies: response.total_copies,
      });
    } catch (err) {
      const apiError = err as { message?: string };
      setError(apiError.message || "Failed to fetch book");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchBook();
  }, [bookId]);

  const handleSave = async () => {
    setIsSaving(true);
    setError(null);
    try {
      await booksApi.update(bookId, formData);
      setIsEditing(false);
      await fetchBook();
    } catch (err) {
      const apiError = err as { message?: string };
      setError(apiError.message || "Failed to update book");
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async () => {
    try {
      await booksApi.delete(bookId);
      router.push("/books");
    } catch (err) {
      const apiError = err as { message?: string };
      setError(apiError.message || "Failed to delete book");
      setShowDeleteDialog(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: name === "total_copies" ? parseInt(value, 10) || 0 : value,
    });
  };

  if (isLoading) {
    return <div className="text-center py-8">Loading...</div>;
  }

  if (!book) {
    return (
      <div className="text-center py-8 text-red-600">
        Book not found
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Book Details</h1>
        <div className="space-x-2">
          {isEditing ? (
            <>
              <button
                type="button"
                onClick={() => setIsEditing(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSave}
                disabled={isSaving}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {isSaving ? "Saving..." : "Save"}
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                onClick={() => setIsEditing(true)}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                Edit
              </button>
              <button
                type="button"
                onClick={() => setShowDeleteDialog(true)}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
              >
                Delete
              </button>
            </>
          )}
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

      <div className="bg-white rounded-lg shadow-md p-6">
        {isEditing ? (
          <form>
            <FormField
              id="isbn"
              name="isbn"
              label="ISBN"
              type="text"
              value={formData.isbn || ""}
              onChange={handleChange}
              required
            />
            <FormField
              id="title"
              name="title"
              label="Title"
              type="text"
              value={formData.title || ""}
              onChange={handleChange}
              required
            />
            <FormField
              id="author"
              name="author"
              label="Author"
              type="text"
              value={formData.author || ""}
              onChange={handleChange}
              required
            />
            <FormField
              id="total_copies"
              name="total_copies"
              label="Total Copies"
              type="number"
              value={formData.total_copies || 0}
              onChange={handleChange}
              required
              min="1"
            />
          </form>
        ) : (
          <div className="space-y-4">
            <div>
              <span className="font-semibold text-gray-700">ISBN:</span>
              <span className="ml-2 text-gray-900">{book.isbn}</span>
            </div>
            <div>
              <span className="font-semibold text-gray-700">Title:</span>
              <span className="ml-2 text-gray-900">{book.title}</span>
            </div>
            <div>
              <span className="font-semibold text-gray-700">Author:</span>
              <span className="ml-2 text-gray-900">{book.author}</span>
            </div>
            <div>
              <span className="font-semibold text-gray-700">Total Copies:</span>
              <span className="ml-2 text-gray-900">{book.total_copies}</span>
            </div>
            <div>
              <span className="font-semibold text-gray-700">Available:</span>
              <span className="ml-2 text-gray-900">{book.available}</span>
            </div>
            <div>
              <span className="font-semibold text-gray-700">Created:</span>
              <span className="ml-2 text-gray-900">
                {new Date(book.created_at).toLocaleString()}
              </span>
            </div>
            <div>
              <span className="font-semibold text-gray-700">Last Updated:</span>
              <span className="ml-2 text-gray-900">
                {new Date(book.updated_at).toLocaleString()}
              </span>
            </div>
          </div>
        )}
      </div>

      <ConfirmDialog
        isOpen={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        onConfirm={handleDelete}
        title="Delete Book"
        message={`Are you sure you want to delete "${book.title}"? This action cannot be undone.`}
        confirmText="Delete"
        cancelText="Cancel"
      />
    </div>
  );
}
