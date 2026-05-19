/** Status badge component for displaying loan status with color coding. */

import { LoanStatus } from "@/lib/api";

interface StatusBadgeProps {
  status: LoanStatus;
}

const statusStyles: Record<LoanStatus, string> = {
  [LoanStatus.ACTIVE]: "bg-blue-100 text-blue-800 border-blue-200",
  [LoanStatus.RETURNED]: "bg-green-100 text-green-800 border-green-200",
  [LoanStatus.OVERDUE]: "bg-red-100 text-red-800 border-red-200",
};

export function StatusBadge({ status }: StatusBadgeProps) {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${statusStyles[status]}`}
      role="status"
      aria-label={`Loan status: ${status}`}
    >
      {status}
    </span>
  );
}
