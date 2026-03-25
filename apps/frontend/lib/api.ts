import { env } from "./env";

async function fetchJson<T>(input: string, init?: RequestInit): Promise<T> {
  const response = await fetch(input, init);

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return (await response.json()) as T;
}

export const apiClient = {
  getBackendHealth() {
    return fetchJson<{ status: string; service: string }>(
      `${env.backendUrl}/api/health`,
    );
  },
  getMlHealth() {
    return fetchJson<{ status: string; service: string }>(
      `${env.mlApiUrl}/ml/health`,
    );
  },
  // TODO: Add typed methods for dashboard, customers, churn, recommendations, and forecast endpoints.
};
