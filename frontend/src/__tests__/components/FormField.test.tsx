/** Tests for FormField component. */

import { render, screen } from "@testing-library/react";
import { FormField } from "@/components/FormField";

describe("FormField", () => {
  it("renders label and input correctly", () => {
    render(<FormField id="test" name="test" label="Test Label" />);
    expect(screen.getByLabelText("Test Label")).toBeInTheDocument();
  });

  it("shows error message when provided", () => {
    render(
      <FormField
        id="test"
        name="test"
        label="Test Label"
        error="This field is required"
      />,
    );
    expect(screen.getByText("This field is required")).toBeInTheDocument();
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("applies error styling when error is present", () => {
    render(
      <FormField
        id="test"
        name="test"
        label="Test Label"
        error="This field is required"
      />,
    );
    const input = screen.getByLabelText("Test Label");
    expect(input).toHaveClass("border-red-500");
  });

  it("has proper ARIA attributes for accessibility", () => {
    render(
      <FormField
        id="test"
        name="test"
        label="Test Label"
        error="This field is required"
      />,
    );
    const input = screen.getByLabelText("Test Label");
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(input).toHaveAttribute("aria-describedby", "test-error");
  });

  it("passes additional props to input", () => {
    render(
      <FormField
        id="test"
        name="test"
        label="Test Label"
        type="email"
        placeholder="test@example.com"
      />,
    );
    const input = screen.getByLabelText("Test Label");
    expect(input).toHaveAttribute("type", "email");
    expect(input).toHaveAttribute("placeholder", "test@example.com");
  });
});
