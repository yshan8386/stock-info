function resolveApiUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_URL;
  if (typeof window === "undefined") {
    return configured ?? "http://localhost:8000/api/v1";
  }

  const currentHost = window.location.hostname;
  if (!configured) {
    return `http://${currentHost}:8000/api/v1`;
  }

  try {
    const url = new URL(configured);
    if (["localhost", "127.0.0.1"].includes(url.hostname)) {
      url.hostname = currentHost;
      return url.toString().replace(/\/$/, "");
    }
  } catch {
    // Keep the configured value if it is not a valid absolute URL.
  }

  return configured;
}

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number
  ) {
    super(message);
  }
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${resolveApiUrl()}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...init.headers
    }
  });

  if (!response.ok) {
    let message = response.statusText;
    try {
      const data = await response.json();
      message = data?.error?.message ?? data?.detail ?? message;
    } catch {
      // Keep the HTTP status text.
    }
    throw new ApiError(message, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export function formatDate(date: string): string {
  return new Intl.DateTimeFormat("ko-KR", {
    year: "numeric",
    month: "long",
    day: "numeric",
    weekday: "long"
  }).format(new Date(date));
}
