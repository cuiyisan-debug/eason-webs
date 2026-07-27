const JSON_HEADERS = {
  "content-type": "application/json; charset=utf-8",
  "cache-control": "no-store, max-age=0",
};

const MAX_ADMIN_PAGE_SIZE = 200;
const CLIENT_ID_PATTERN = /^[a-z0-9-]{12,80}$/i;

function json(payload, status = 200, headers = {}) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { ...JSON_HEADERS, ...headers },
  });
}

function corsHeaders(request, env) {
  const origin = request.headers.get("Origin") || "";
  const allowed = String(env.VISITOR_ALLOWED_ORIGINS || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);

  if (!origin || !allowed.includes(origin)) {
    return {};
  }

  return {
    "access-control-allow-origin": origin,
    "access-control-allow-methods": "GET, POST, OPTIONS",
    "access-control-allow-headers": "content-type, authorization",
    "access-control-max-age": "86400",
    vary: "Origin",
  };
}

function maskIp(ip) {
  if (!ip) return "";
  if (/^\d{1,3}(\.\d{1,3}){3}$/.test(ip)) {
    const parts = ip.split(".");
    return `${parts[0]}.${parts[1]}.${parts[2]}.*`;
  }
  const parts = ip.split(":").filter(Boolean);
  return parts.length ? `${parts.slice(0, 3).join(":")}::*` : "";
}

async function sha256Hex(value) {
  const data = new TextEncoder().encode(value);
  const digest = await crypto.subtle.digest("SHA-256", data);
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

function safePath(value) {
  const text = String(value || "/").slice(0, 240);
  return text.startsWith("/") ? text : "/";
}

function safeReferrer(value) {
  return String(value || "").slice(0, 320);
}

function safeUserAgent(value) {
  return String(value || "").slice(0, 240);
}

function todayKey(now = new Date()) {
  return now.toISOString().slice(0, 10);
}

async function readPayload(request) {
  if (request.method === "GET") {
    const url = new URL(request.url);
    return {
      clientId: url.searchParams.get("cid") || "",
      path: url.searchParams.get("path") || "/",
      referrer: url.searchParams.get("referrer") || "",
    };
  }

  const contentType = request.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) return {};

  try {
    return await request.json();
  } catch {
    return {};
  }
}

function hasAdminAccess(request, env) {
  const expected = env.VISITOR_ADMIN_TOKEN;
  if (!expected) return false;
  const header = request.headers.get("Authorization") || "";
  return header === `Bearer ${expected}`;
}

export class VisitorCounter {
  constructor(state, env) {
    this.state = state;
    this.env = env;
  }

  async fetch(request) {
    const url = new URL(request.url);
    if (url.pathname.endsWith("/admin")) {
      return this.handleAdmin(request, url);
    }

    if (request.method !== "GET" && request.method !== "POST") {
      return json({ ok: false, error: "method_not_allowed" }, 405);
    }

    const payload = await readPayload(request);
    const clientId = CLIENT_ID_PATTERN.test(String(payload.clientId || "")) ? String(payload.clientId) : "";
    const ip = request.headers.get("CF-Connecting-IP") || "";
    const country = request.headers.get("CF-IPCountry") || "";
    const userAgent = safeUserAgent(request.headers.get("User-Agent"));
    const now = new Date();
    const day = todayKey(now);
    const path = safePath(payload.path);
    const referrer = safeReferrer(payload.referrer);
    const ipHashSalt = this.env.VISITOR_IP_HASH_SALT || this.env.VISITOR_ADMIN_TOKEN || "mycys-visitor-counter";
    const ipHash = ip ? await sha256Hex(`${ipHashSalt}:${ip}`) : "";
    const storeFullIp = String(this.env.VISITOR_STORE_FULL_IP || "").toLowerCase() === "true";

    let stats = (await this.state.storage.get("stats")) || {
      pv: 0,
      uv: 0,
      visitSeq: 0,
      startedAt: now.toISOString(),
      updatedAt: "",
    };
    stats.pv += 1;
    stats.visitSeq = Number(stats.visitSeq || 0) + 1;
    stats.updatedAt = now.toISOString();

    if (clientId) {
      const seenKey = `seen:${clientId}`;
      const seen = await this.state.storage.get(seenKey);
      if (!seen) {
        stats.uv += 1;
        await this.state.storage.put(seenKey, now.toISOString());
      }
    }

    const dayKey = `day:${day}`;
    const daily = (await this.state.storage.get(dayKey)) || { date: day, pv: 0, uv: 0 };
    daily.pv += 1;
    if (clientId) {
      const dailySeenKey = `seen:${day}:${clientId}`;
      const dailySeen = await this.state.storage.get(dailySeenKey);
      if (!dailySeen) {
        daily.uv += 1;
        await this.state.storage.put(dailySeenKey, now.toISOString());
      }
    }

    const visit = {
      seq: stats.visitSeq,
      at: now.toISOString(),
      path,
      referrer,
      country,
      ip: storeFullIp ? ip : "",
      maskedIp: maskIp(ip),
      ipHash: ipHash.slice(0, 24),
      userAgent,
    };

    await this.state.storage.put("stats", stats);
    await this.state.storage.put(dayKey, daily);
    await this.state.storage.put(`visit:${stats.visitSeq}`, visit);

    return json({
      ok: true,
      site: {
        pv: stats.pv,
        uv: stats.uv,
      },
      today: {
        pv: daily.pv,
        uv: daily.uv,
      },
      updatedAt: stats.updatedAt,
    });
  }

  async handleAdmin(request, url) {
    if (!hasAdminAccess(request, this.env)) {
      return json({ ok: false, error: "unauthorized" }, 401);
    }

    const limit = Math.min(Math.max(Number(url.searchParams.get("limit") || 100), 1), MAX_ADMIN_PAGE_SIZE);
    const revealIp = url.searchParams.get("reveal") === "1";
    const stats = (await this.state.storage.get("stats")) || { pv: 0, uv: 0, visitSeq: 0 };
    const startBefore = Math.min(Number(url.searchParams.get("before") || Number(stats.visitSeq) + 1), Number(stats.visitSeq) + 1);
    const visits = [];

    let cursor = startBefore;
    while (cursor > 1 && visits.length < limit) {
      cursor -= 1;
      const item = await this.state.storage.get(`visit:${cursor}`);
      if (item) {
        visits.push({
          ...item,
          ip: revealIp ? item.ip || "" : "",
        });
      }
    }

    return json({
      ok: true,
      site: stats,
      visits,
      nextBefore: cursor > 1 ? cursor : null,
    });
  }
}

export default {
  async fetch(request, env) {
    const cors = corsHeaders(request, env);
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: cors });
    }

    const url = new URL(request.url);
    if (!url.pathname.startsWith("/api/visitor-stats")) {
      return json({ ok: false, error: "not_found" }, 404, cors);
    }

    const id = env.VISITOR_COUNTER.idFromName("global");
    const object = env.VISITOR_COUNTER.get(id);
    const response = await object.fetch(request);
    return new Response(response.body, {
      status: response.status,
      headers: { ...Object.fromEntries(response.headers), ...cors },
    });
  },
};
