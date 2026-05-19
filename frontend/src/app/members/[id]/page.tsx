/** Member detail page with edit form and active loans list. */

"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { membersApi, loansApi } from "@/lib/api";
import type { MemberResponse, MemberUpdate, LoanResponse } from "@/lib/api";
import { FormField } from "@/components/FormField";
import { ConfirmDialog } from "@/components/ConfirmDialog";
import { StatusBadge } from "@/components/StatusBadge";

export default function MemberDetailPage() {
  const router = useRouter();
  const params = useParams();
  const memberId = params.id as string;

  const [member, setMember] = useState<MemberResponse | null>(null);
  const [activeLoans, setActiveLoans] = useState<LoanResponse[]>([]);
  const [isEditing, setIsEditing] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [formData, setFormData] = useState<MemberUpdate>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchMember = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await membersApi.get(memberId);
      setMember(response);
      setFormData({
        name: response.name,
        email: response.email,
        phone: response.phone || "",
      });
    } catch (err) {
      const apiError = err as { message?: string };
      setError(apiError.message || "Failed to fetch member");
    } finally {
      setIsLoading(false);
    }
  };

  const fetchActiveLoans = async () => {
    try {
      const response = await loansApi.list({
        member_id: memberId,
        status: "ACTIVE" as any,
      });
      setActiveLoans(response.items);
    } catch (err) {
      console.error("Failed to fetch active loans:", err);
    }
  };

  useEffect(() => {
    fetchMember();
    fetchActiveLoans();
  }, [memberId]);

  const handleSave = async () => {
    setIsSaving(true);
    setError(null);
    try {
      await membersApi.update(memberId, formData);
      setIsEditing(false);
      await fetchMember();
    } catch (err) {
      const apiError = err as { message?: string };
      setError(apiError.message || "Failed to update member");
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async () => {
    try {
      await membersApi.delete(memberId);
      router.push("/members");
    } catch (err) {
      const apiError = err as { message?: string };
      setError(apiError.message || "Failed to delete member");
      setShowDeleteDialog(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value,
    });
  };

  if (isLoading) {
    return <div className="text-center py-8">Loading...</div>;
  }

  if (!member) {
    return <div className="text-center py-8 text-red-600">Member not found</div>;
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Member Details</h1>
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

      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        {isEditing ? (
          <form>
            <FormField
              id="name"
              name="name"
              label="Name"
              type="text"
              value={formData.name || ""}
              onChange={handleChange}
              required
            />
            <FormField
              id="email"
              name="email"
              label="Email"
              type="email"
              value={formData.email || ""}
              onChange={handleChange}
              required
            />
            <FormField
              id="phone"
              name="phone"
              label="Phone"
              type="text"
              value={formData.phone || ""}
              onChange={handleChange}
            />
          </form>
        ) : (
          <div className="space-y-4">
            <div>
              <span className="font-semibold text-gray-700">Name:</span>
              <span className="ml-2 text-gray-900">{member.name}</span>
            </div>
            <div>
              <span className="font-semibold text-gray-700">Email:</span>
              <span className="ml-2 text-gray-900">{member.email}</span>
            </div>
            <div>
              <span className="font-semibold text-gray-700">Phone:</span>
              <span className="ml-2 text-gray-900">{member.phone || "N/A"}</span>
            </div>
            <div>
              <span className="font-semibold text-gray-700">Status:</span>
              <span className="ml-2">
                {member.is_active ? (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    Active
                  </span>
                ) : (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                    Inactive
                  </span>
                )}
              </span>
            </div>
            <div>
              <span className="font-semibold text-gray-700">Joined:</span>
              <span className="ml-2 text-gray-900">
                {new Date(member.joined_at).toLocaleString()}
              </span>
            </div>
          </div>
        )}
      </div>

      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Active Loans ({activeLoans.length})
        </h2>
        {activeLoans.length === 0 ? (
          <p className="text-gray-500">No active loans</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Book ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Borrowed
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Due Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {activeLoans.map((loan) => (
                  <tr key={loan.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {loan.book_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {new Date(loan.borrowed_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {new Date(loan.due_date).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <StatusBadge status={loan.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <ConfirmDialog
        isOpen={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        onConfirm={handleDelete}
        title="Delete Member"
        message={`Are you sure you want to delete "${member.name}"? This action cannot be undone.`}
        confirmText="Delete"
        cancelText="Cancel"
      />
    </div>
  );
}
