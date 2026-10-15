import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const endpoint = path.join("/");
  const allowed = /^(status|search|import\/(json|url)|events\/[a-zA-Z0-9-]+(?:\/brief)?)$/;
  if (!allowed.test(endpoint)) return NextResponse.json({ detail: "Not found" }, { status: 404 });
  if (request.method === "POST") {
    const origin = request.headers.get("origin");
    // Next can normalize the internal URL to localhost even when the browser uses
    // 127.0.0.1. Compare against the incoming Host, which browsers cannot override.
    if (origin) {
      try {
        const parsed = new URL(origin);
        if (!["http:", "https:"].includes(parsed.protocol) || parsed.host !== request.headers.get("host"))
          return NextResponse.json({ detail: "Cross-origin request rejected" }, { status: 403 });
      } catch {
        return NextResponse.json({ detail: "Invalid origin" }, { status: 403 });
      }
    }
    if (!request.headers.get("content-type")?.includes("application/json")) return NextResponse.json({ detail: "Send JSON" }, { status: 415 });
  }
  try {
    const chunks: Uint8Array[] = [];
    let size = 0;
    if (request.body) {
      const reader = request.body.getReader();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        size += value.byteLength;
        if (size > 1_000_000) { await reader.cancel(); return NextResponse.json({ detail: "Request exceeds 1 MB" }, { status: 413 }); }
        chunks.push(value);
      }
    }
    const backend = (process.env.BACKEND_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
    const response = await fetch(`${backend}/v1/${endpoint}`, {
      method: request.method,
      headers: { "Content-Type": "application/json", ...(process.env.HACKRADAR_API_TOKEN ? { "X-API-Token": process.env.HACKRADAR_API_TOKEN } : {}) },
      body: request.method === "GET" ? undefined : Buffer.concat(chunks),
      cache: "no-store", signal: AbortSignal.timeout(50_000), redirect: "error",
    });
    return new NextResponse(await response.text(), { status: response.status, headers: { "Content-Type": "application/json", "Cache-Control": "no-store" } });
  } catch {
    return NextResponse.json({ detail: "Cannot reach HackRadar’s API. Start the FastAPI backend on port 8000 and retry." }, { status: 503 });
  }
}

export { proxy as GET, proxy as POST };
