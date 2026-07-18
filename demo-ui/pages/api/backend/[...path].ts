import type { NextApiRequest, NextApiResponse } from "next";

const BACKEND_BASE_URL = process.env.API_BASE_URL?.replace(/\/$/, "");
const BACKEND_API_KEY = process.env.BACKEND_API_KEY;

export default async function backendProxy(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== "GET") return res.status(405).json({ detail: "Method not allowed" });
  if (!BACKEND_BASE_URL || !BACKEND_API_KEY) {
    return res.status(500).json({ detail: "Demo backend is not configured" });
  }

  const path = req.query.path;
  if (!Array.isArray(path) || path[0] !== "v1") {
    return res.status(404).json({ detail: "Unknown API path" });
  }

  const target = new URL(`${BACKEND_BASE_URL}/${path.map(encodeURIComponent).join("/")}`);
  for (const [key, value] of Object.entries(req.query)) {
    if (key === "path") continue;
    for (const item of Array.isArray(value) ? value : [value]) {
      if (typeof item === "string") target.searchParams.append(key, item);
    }
  }

  try {
    const upstream = await fetch(target, {
      headers: { Authorization: `Bearer ${BACKEND_API_KEY}` },
    });
    const body = await upstream.text();
    const contentType = upstream.headers.get("content-type");
    if (contentType) res.setHeader("Content-Type", contentType);
    return res.status(upstream.status).send(body);
  } catch {
    return res.status(502).json({ detail: "Demo backend is unavailable" });
  }
}
