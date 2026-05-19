/** Tests for DataTable component. */

import { render, screen, fireEvent } from "@testing-library/react";
import { DataTable } from "@/components/DataTable";
import type { Column } from "@/components/DataTable";

interface TestItem {
  id: number;
  name: string;
  value: number;
}

describe("DataTable", () => {
  const columns: Column<TestItem>[] = [
    { key: "id", label: "ID", sortable: true },
    { key: "name", label: "Name", sortable: true },
    { key: "value", label: "Value", sortable: true },
  ];

  const testData: TestItem[] = [
    { id: 1, name: "Item 1", value: 100 },
    { id: 2, name: "Item 2", value: 200 },
    { id: 3, name: "Item 3", value: 300 },
  ];

  it("renders table with data", () => {
    render(<DataTable columns={columns} data={testData} />);
    expect(screen.getByText("ID")).toBeInTheDocument();
    expect(screen.getByText("Name")).toBeInTheDocument();
    expect(screen.getByText("Value")).toBeInTheDocument();
    expect(screen.getByText("Item 1")).toBeInTheDocument();
    expect(screen.getByText("Item 2")).toBeInTheDocument();
    expect(screen.getByText("Item 3")).toBeInTheDocument();
  });

  it("renders empty state when no data", () => {
    render(<DataTable columns={columns} data={[]} />);
    expect(screen.getByText("No data available")).toBeInTheDocument();
  });

  it("renders loading state when isLoading is true", () => {
    render(<DataTable columns={columns} data={[]} isLoading={true} />);
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("calls onSort when sortable column header is clicked", () => {
    const onSort = jest.fn();
    render(<DataTable columns={columns} data={testData} onSort={onSort} />);
    const header = screen.getByText("Name");
    fireEvent.click(header);
    expect(onSort).toHaveBeenCalledWith("name");
  });

  it("does not call onSort when non-sortable column is clicked", () => {
    const onSort = jest.fn();
    const nonSortableColumns: Column<TestItem>[] = [
      { key: "id", label: "ID", sortable: false },
      { key: "name", label: "Name", sortable: false },
    ];
    render(<DataTable columns={nonSortableColumns} data={testData} onSort={onSort} />);
    const header = screen.getByText("Name");
    fireEvent.click(header);
    expect(onSort).not.toHaveBeenCalled();
  });

  it("shows sort indicator when column is sorted", () => {
    render(
      <DataTable
        columns={columns}
        data={testData}
        onSort={jest.fn()}
        sortKey="name"
        sortDirection="asc"
      />,
    );
    const header = screen.getByText("Name");
    expect(header.textContent).toContain("↑");
  });

  it("calls onNextPage when Load More button is clicked", () => {
    const onNextPage = jest.fn();
    render(
      <DataTable columns={columns} data={testData} onNextPage={onNextPage} hasNextPage={true} />,
    );
    const button = screen.getByText("Load More");
    fireEvent.click(button);
    expect(onNextPage).toHaveBeenCalledTimes(1);
  });

  it("does not show Load More button when hasNextPage is false", () => {
    render(
      <DataTable columns={columns} data={testData} onNextPage={jest.fn()} hasNextPage={false} />,
    );
    expect(screen.queryByText("Load More")).not.toBeInTheDocument();
  });

  it("uses custom render function when provided", () => {
    const customColumns: Column<TestItem>[] = [
      {
        key: "value",
        label: "Value",
        render: (value) => <span>${value as number}</span>,
      },
    ];
    render(<DataTable columns={customColumns} data={testData} />);
    expect(screen.getByText("$100")).toBeInTheDocument();
    expect(screen.getByText("$200")).toBeInTheDocument();
  });

  it("has proper ARIA attributes for sorting", () => {
    render(
      <DataTable
        columns={columns}
        data={testData}
        onSort={jest.fn()}
        sortKey="name"
        sortDirection="asc"
      />,
    );
    const header = screen.getByText("Name").closest("th");
    expect(header).toHaveAttribute("aria-sort", "ascending");
  });
});
