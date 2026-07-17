export type Insight = {
  tenant_id: string;
  pair_id: string;
  student_ref: string;
  timestamp: string;
  decision: "escalate" | "retire" | "no_change";
  reasoning: string;
};

export type Attempt = {
  timestamp: string;
  correct: boolean;
  context: string | null;
  episode_uuid: string;
};

export type Pair = {
  id: string;
  tenant_id: string;
  domain: string;
  label_a: string;
  label_b: string;
  description?: string | null;
};

export type PairState = {
  pair_id: string;
  recent_facts: Attempt[];
  graph_facts: unknown[];
  latest_insight: Insight | null;
};

const baseUrl = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");
const apiKey = process.env.NEXT_PUBLIC_API_KEY;

async function request<T>(path: string): Promise<T> {
  if (!apiKey) throw new Error("Set NEXT_PUBLIC_API_KEY in demo-ui/.env.local to load live demo data.");
  const response = await fetch(`${baseUrl}${path}`, {
    headers: { Authorization: `Bearer ${apiKey}` }
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`API ${response.status}: ${detail}`);
  }
  return response.json() as Promise<T>;
}

export const getPairState = (pairId: string) =>
  request<PairState>(`/v1/state/${encodeURIComponent(pairId)}?tenant_id=demo-school&student_ref=demo-student-1`);

export const getInsightFeed = (pairId: string) =>
  request<Insight[]>(`/v1/insights/${encodeURIComponent(pairId)}/history?tenant_id=demo-school&student_ref=demo-student-1`);

export const getPairs = (domain: string) => request<Pair[]>(`/v1/pairs?domain=${encodeURIComponent(domain)}`);
