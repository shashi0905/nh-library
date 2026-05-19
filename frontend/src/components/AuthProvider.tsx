"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";

const publicPaths = ["/login"];

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const checkAuth = () => {
      const token = localStorage.getItem("access_token");
      const isPublicPath = publicPaths.some((path) => pathname.startsWith(path));
      
      if (!token && !isPublicPath) {
        router.push("/login");
      } else if (token && isPublicPath) {
        router.push("/");
      } else {
        setIsAuthenticated(!!token);
      }
      setIsLoading(false);
    };

    checkAuth();
  }, [pathname, router]);

  if (isLoading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  }

  if (!isAuthenticated && !publicPaths.some((path) => pathname.startsWith(path))) {
    return null;
  }

  return <>{children}</>;
}

export function useAuth() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    setIsAuthenticated(!!token);
  }, []);

  return { isAuthenticated };
}
