export type Interest = "AI Agents" | "FDE" | "Startups" | "Open Source" | "Climate Tech";
export type Preferences = { city: string; interests: Interest[]; days: number; min_score: number; include_online: boolean; include_examples: boolean };
export type Event = { id: string; title: string; description: string; start_at: string; end_at: string | null; city: string; venue: string; url: string; organizer: string; tags: string[]; format: "in_person" | "online" | "hybrid"; kind: string; cost: string; provenance: "example" | "public_import" | "user_import"; source_urls: string[]; retrieved_at: string | null };
export type Dimension = { label: string; earned: number; possible: number; evidence: string };
export type Score = { total: number; engine: string; dimensions: Dimension[]; matched_interests: string[]; eligible: boolean; exclusions: string[] };
export type RankedEvent = { event: Event; score: Score };
export type SearchResult = { results: RankedEvent[]; total_scanned: number; matching: number; examples: number; imported: number; as_of: string; timezone: string };
export type Brief = { provider: "local" | "grok"; notice: string; summary: string; application_pitch: string; preparation: string[] };
export const INTERESTS: Interest[] = ["AI Agents", "FDE", "Startups", "Open Source", "Climate Tech"];
export const DEFAULTS: Preferences = { city: "London", interests: ["AI Agents", "FDE", "Startups"], days: 30, min_score: 7, include_online: false, include_examples: true };

export async function api<T>(path: string, body?: unknown, signal?: AbortSignal): Promise<T> {
  const res = await fetch(`/api/${path}`, { method: body === undefined ? "GET" : "POST", headers: { "Content-Type": "application/json" }, body: body === undefined ? undefined : JSON.stringify(body), signal });
  const data = await res.json();
  if (!res.ok) {
    const detail = Array.isArray(data.detail) ? data.detail.map((e: { loc: string[]; msg: string }) => `${e.loc.join(".")}: ${e.msg}`).join("; ") : data.detail;
    throw new Error(detail || "Something went wrong. Please try again.");
  }
  return data;
}
