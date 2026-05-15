import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Neighborhood Library",
  description: "Library management for staff",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
