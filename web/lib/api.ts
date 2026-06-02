export type ApiOpts = { method?: string; token?: string; body?: unknown };

export async function api<T = any>(path: string, opts: ApiOpts = {}): Promise<T> {
  const res = await fetch(`/api${path}`, {
    method: opts.method || "GET",
    headers: {
      "Content-Type": "application/json",
      ...(opts.token ? { Authorization: `Bearer ${opts.token}` } : {}),
    },
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const message = (data && data.detail && data.detail.message) || `HTTP ${res.status}`;
    throw new Error(message);
  }
  return data as T;
}
