const BASE = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, '');

const API_BASE = import.meta.env.PROD ? '' : BASE;

export const hasBackend = import.meta.env.PROD || Boolean(API_BASE);

export async function http<T>(path: string, init?: RequestInit): Promise<T> {
  if (API_BASE === undefined) {
    throw new Error('VITE_API_URL is not set. Configure the backend URL in .env.');
  }

  const headers = new Headers(init?.headers);

  if (!headers.has('Content-Type') && init?.body !== undefined) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
  });

  if (!response.ok) {
    const detail = await response.text().catch(() => '');
    throw new Error(
      `API request failed (${response.status})${detail ? `: ${detail}` : ''}`,
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}
