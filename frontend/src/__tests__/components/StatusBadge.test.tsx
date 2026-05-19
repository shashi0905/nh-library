/** Tests for StatusBadge component. */

import { render, screen } from "@testing-library/react";
import { StatusBadge } from "@/components/StatusBadge";
import { LoanStatus } from "@/lib/api";

describe("StatusBadge", () => {
  it("renders ACTIVE status with correct styling", () => {
    render(<StatusBadge status={LoanStatus.ACTIVE} />);
    const badge = screen.getByRole("status");
    expect(badge).toHaveTextContent("ACTIVE");
    expect(badge).toHaveClass("bg-blue-100", "text-blue-800");
  });

  it("renders RETURNED status with correct styling", () => {
    render(<StatusBadge status={LoanStatus.RETURNED} />);
    const badge = screen.getByRole("status");
    expect(badge).toHaveTextContent("RETURNED");
    expect(badge).toHaveClass("bg-green-100", "text-green-800");
  });

  it("renders OVERDUE status with correct styling", () => {
    render(<StatusBadge status={LoanStatus.OVERDUE} />);
    const badge = screen.getByRole("status");
    expect(badge).toHaveTextContent("OVERDUE");
    expect(badge).toHaveClass("bg-red-100", "text-red-800");
  });

  it("has proper ARIA label", () => {
    render(<StatusBadge status={LoanStatus.ACTIVE} />);
    const badge = screen.getByRole("status");
    expect(badge).toHaveAttribute("aria-label", "Loan status: ACTIVE");
  });
});
