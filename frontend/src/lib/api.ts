import type {
  CascadeRequest,
  CascadeResponse,
  GraphResponse,
  PredictRequest,
  PredictResponse,
  Vessel,
} from "@/lib/types";

const DEFAULT_API_BASE = "https://cascadeiq-api.onrender.com";

export function apiBaseUrl() {
  return process.env.NEXT_PUBLIC_API_BASE_URL || DEFAULT_API_BASE;
}

async function jsonFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${apiBaseUrl()}${path}`;
  const res = await fetch(url, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status} ${res.statusText}: ${text}`);
  }
  return (await res.json()) as T;
}

export async function fetchVessels(): Promise<Vessel[]> {
  const data = await jsonFetch<{ vessels: Vessel[] }>("/vessels");
  return data.vessels;
}

export async function predictDelay(req: PredictRequest): Promise<PredictResponse> {
  return await jsonFetch<PredictResponse>("/predict", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export async function fetchGraph(): Promise<GraphResponse> {
  return await jsonFetch<GraphResponse>("/graph");
}

export async function runCascade(req: CascadeRequest): Promise<CascadeResponse> {
  return await jsonFetch<CascadeResponse>("/cascade", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

