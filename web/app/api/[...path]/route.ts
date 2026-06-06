// Runtime proxy to the FastAPI product API. Reads AEDIFICA_API at REQUEST time
// (server-side route handlers are not build-baked), so the same image works in
// dev (localhost) and in compose/prod (http://api:8090, the deployed URL, ...).
export const dynamic = "force-dynamic";

const API = () => process.env.AEDIFICA_API || "http://127.0.0.1:8090";

async function proxy(req: Request, path: string[]) {
  const search = new URL(req.url).search;
  const url = `${API()}/api/${path.join("/")}${search}`;
  const headers: Record<string, string> = {};
  const auth = req.headers.get("authorization");
  const ctype = req.headers.get("content-type");
  if (auth) headers["authorization"] = auth;
  if (ctype) headers["content-type"] = ctype;

  const init: RequestInit = { method: req.method, headers };
  if (req.method !== "GET" && req.method !== "HEAD") {
    init.body = await req.text();
  }
  const res = await fetch(url, init);
  const body = await res.text();
  return new Response(body, {
    status: res.status,
    headers: { "content-type": res.headers.get("content-type") || "application/json" },
  });
}

type Ctx = { params: { path: string[] } };
export async function GET(req: Request, ctx: Ctx) {
  return proxy(req, ctx.params.path);
}
export async function POST(req: Request, ctx: Ctx) {
  return proxy(req, ctx.params.path);
}
// Verbs used by the workspace: PATCH for status toggles (checklist ticks, task done,
// BRS lock, document validation level…), PUT for full replaces, DELETE for removals.
// Without these, Next.js answers 405 before FastAPI ever sees the request.
export async function PATCH(req: Request, ctx: Ctx) {
  return proxy(req, ctx.params.path);
}
export async function PUT(req: Request, ctx: Ctx) {
  return proxy(req, ctx.params.path);
}
export async function DELETE(req: Request, ctx: Ctx) {
  return proxy(req, ctx.params.path);
}
