/** Typed API client for Neighborhood Library backend. */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/** Custom error class for API errors. */
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public detail?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/** Loan status enum matching backend. */
export enum LoanStatus {
  ACTIVE = "ACTIVE",
  RETURNED = "RETURNED",
  OVERDUE = "OVERDUE",
}

// ============================================================================
// Type Definitions (mirroring backend Pydantic schemas)
// ============================================================================

/** Book request/response types. */
export interface BookCreate {
  isbn: string;
  title: string;
  author: string;
  total_copies?: number;
}

export interface BookUpdate {
  isbn?: string;
  title?: string;
  author?: string;
  total_copies?: number;
}

export interface BookResponse {
  id: string;
  isbn: string;
  title: string;
  author: string;
  total_copies: number;
  available: number;
  created_at: string;
  updated_at: string;
}

export interface BookListResponse {
  items: BookResponse[];
  next_cursor: string | null;
}

/** Member request/response types. */
export interface MemberCreate {
  name: string;
  email: string;
  phone?: string;
}

export interface MemberUpdate {
  name?: string;
  email?: string;
  phone?: string;
}

export interface MemberResponse {
  id: string;
  name: string;
  email: string;
  phone: string | null;
  joined_at: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface MemberListResponse {
  items: MemberResponse[];
  next_cursor: string | null;
}

/** Loan request/response types. */
export interface LoanCreate {
  book_id: string;
  member_id: string;
}

export interface LoanResponse {
  id: string;
  book_id: string;
  member_id: string;
  borrowed_at: string;
  due_date: string;
  returned_at: string | null;
  status: LoanStatus;
  fine_amount: string | null;
  fine_paid: boolean;
  created_at: string;
}

export interface LoanListResponse {
  items: LoanResponse[];
  next_cursor: string | null;
}

/** Authentication types. */
export interface TokenRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

// ============================================================================
// API Client
// ============================================================================

/** Helper function to make authenticated API requests. */
async function fetchWithAuth(
  endpoint: string,
  options: RequestInit = {},
): Promise<Response> {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  // Add Authorization header if token is stored in localStorage
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: "include",
  });

  if (!response.ok) {
    let errorDetail;
    try {
      errorDetail = await response.json();
    } catch {
      errorDetail = await response.text();
    }
    throw new ApiError(
      `API request failed: ${response.statusText}`,
      response.status,
      errorDetail,
    );
  }

  return response;
}

// ============================================================================
// Authentication API
// ============================================================================

export const authApi = {
  /** Login and set httpOnly cookie with access token. */
  async login(credentials: TokenRequest): Promise<TokenResponse> {
    const response = await fetchWithAuth("/api/v1/auth/token", {
      method: "POST",
      body: JSON.stringify(credentials),
    });
    const data = await response.json();
    // Store token in localStorage for Authorization header
    if (typeof window !== "undefined") {
      localStorage.setItem("access_token", data.access_token);
    }
    return data;
  },

  /** Logout by clearing the httpOnly cookie. */
  async logout(): Promise<void> {
    await fetchWithAuth("/api/v1/auth/logout", {
      method: "POST",
    });
    // Clear token from localStorage
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token");
    }
  },

  /** Refresh access token using refresh token. */
  async refreshToken(request: RefreshTokenRequest): Promise<TokenResponse> {
    const response = await fetchWithAuth("/api/v1/auth/refresh", {
      method: "POST",
      body: JSON.stringify(request),
    });
    return response.json();
  },
};

// ============================================================================
// Books API
// ============================================================================

export const booksApi = {
  /** Get a paginated list of books with optional search and cursor. */
  async list(params?: {
    q?: string;
    cursor?: string;
    limit?: number;
  }): Promise<BookListResponse> {
    const queryParams = new URLSearchParams();
    if (params?.q) queryParams.append("q", params.q);
    if (params?.cursor) queryParams.append("cursor", params.cursor);
    if (params?.limit) queryParams.append("limit", params.limit.toString());

    const endpoint = `/api/v1/books${queryParams.toString() ? `?${queryParams.toString()}` : ""}`;
    const response = await fetchWithAuth(endpoint);
    return response.json();
  },

  /** Get a single book by ID. */
  async get(id: string): Promise<BookResponse> {
    const response = await fetchWithAuth(`/api/v1/books/${id}`);
    return response.json();
  },

  /** Create a new book. */
  async create(data: BookCreate): Promise<BookResponse> {
    const response = await fetchWithAuth("/api/v1/books", {
      method: "POST",
      body: JSON.stringify(data),
    });
    return response.json();
  },

  /** Update an existing book. */
  async update(id: string, data: BookUpdate): Promise<BookResponse> {
    const response = await fetchWithAuth(`/api/v1/books/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
    return response.json();
  },

  /** Delete a book. */
  async delete(id: string): Promise<void> {
    await fetchWithAuth(`/api/v1/books/${id}`, {
      method: "DELETE",
    });
  },
};

// ============================================================================
// Members API
// ============================================================================

export const membersApi = {
  /** Get a paginated list of members with optional search and cursor. */
  async list(params?: {
    q?: string;
    cursor?: string;
    limit?: number;
  }): Promise<MemberListResponse> {
    const queryParams = new URLSearchParams();
    if (params?.q) queryParams.append("q", params.q);
    if (params?.cursor) queryParams.append("cursor", params.cursor);
    if (params?.limit) queryParams.append("limit", params.limit.toString());

    const endpoint = `/api/v1/members${queryParams.toString() ? `?${queryParams.toString()}` : ""}`;
    const response = await fetchWithAuth(endpoint);
    return response.json();
  },

  /** Get a single member by ID. */
  async get(id: string): Promise<MemberResponse> {
    const response = await fetchWithAuth(`/api/v1/members/${id}`);
    return response.json();
  },

  /** Register a new member. */
  async create(data: MemberCreate): Promise<MemberResponse> {
    const response = await fetchWithAuth("/api/v1/members", {
      method: "POST",
      body: JSON.stringify(data),
    });
    return response.json();
  },

  /** Update an existing member. */
  async update(id: string, data: MemberUpdate): Promise<MemberResponse> {
    const response = await fetchWithAuth(`/api/v1/members/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
    return response.json();
  },

  /** Delete a member. */
  async delete(id: string): Promise<void> {
    await fetchWithAuth(`/api/v1/members/${id}`, {
      method: "DELETE",
    });
  },
};

// ============================================================================
// Loans API
// ============================================================================

export const loansApi = {
  /** Get a paginated list of loans with optional filters. */
  async list(params?: {
    member_id?: string;
    status?: LoanStatus;
    overdue?: boolean;
    cursor?: string;
    limit?: number;
  }): Promise<LoanListResponse> {
    const queryParams = new URLSearchParams();
    if (params?.member_id) queryParams.append("member_id", params.member_id);
    if (params?.status) queryParams.append("status", params.status);
    if (params?.overdue !== undefined) queryParams.append("overdue", params.overdue.toString());
    if (params?.cursor) queryParams.append("cursor", params.cursor);
    if (params?.limit) queryParams.append("limit", params.limit.toString());

    const endpoint = `/api/v1/loans${queryParams.toString() ? `?${queryParams.toString()}` : ""}`;
    const response = await fetchWithAuth(endpoint);
    return response.json();
  },

  /** Get a single loan by ID. */
  async get(id: string): Promise<LoanResponse> {
    const response = await fetchWithAuth(`/api/v1/loans/${id}`);
    return response.json();
  },

  /** Borrow a book (create a loan). */
  async create(data: LoanCreate): Promise<LoanResponse> {
    const response = await fetchWithAuth("/api/v1/loans", {
      method: "POST",
      body: JSON.stringify(data),
    });
    return response.json();
  },

  /** Return a book. */
  async returnBook(id: string): Promise<LoanResponse> {
    const response = await fetchWithAuth(`/api/v1/loans/${id}/return`, {
      method: "POST",
    });
    return response.json();
  },

  /** Pay a fine for a loan. */
  async payFine(id: string): Promise<LoanResponse> {
    const response = await fetchWithAuth(`/api/v1/loans/${id}/pay-fine`, {
      method: "POST",
    });
    return response.json();
  },
};
