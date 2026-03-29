/**
 * Tollbooth Shortlinks Redirect — serverless GET handler for short URL redirects.
 *
 * Deployed as a Val Town HTTP val.
 *
 * Receives GET /<slug>, looks up the target URL in Neon Postgres,
 * and returns a 302 redirect. No interstitial, no marketing page.
 *
 * Environment variables (set in Val Town):
 *   NEON_DATABASE_URL — Neon connection string
 */

const TTL_SECONDS = 86400; // 24 hours — must match server.py

async function queryNeon(sql, params = []) {
  const connStr = Deno.env.get("NEON_DATABASE_URL");
  if (!connStr) throw new Error("NEON_DATABASE_URL not set");

  const host = new URL(connStr).hostname;
  const resp = await fetch(`https://${host}/sql`, {
    method: "POST",
    headers: {
      "Neon-Connection-String": connStr,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ query: sql, params }),
  });

  if (!resp.ok) {
    throw new Error(`Neon error: ${resp.status} ${await resp.text()}`);
  }
  return resp.json();
}

const NOT_FOUND_HTML = `<!DOCTYPE html>
<html><head><title>Link Not Found</title></head>
<body style="font-family:system-ui,sans-serif;max-width:480px;margin:80px auto;
text-align:center;color:#1a1a1a">
<h1 style="font-size:22px">Link Not Found</h1>
<p style="color:#666">This shortlink doesn\u2019t exist or has expired (links last 24 hours).</p>
</body></html>`;

export default async function handler(req) {
  const url = new URL(req.url);
  const slug = url.pathname.slice(1).toLowerCase().trim();

  if (!slug || slug === "favicon.ico") {
    return new Response(NOT_FOUND_HTML, {
      status: 404,
      headers: { "Content-Type": "text/html" },
    });
  }

  try {
    const result = await queryNeon(
      `SELECT url FROM shortlinks
       WHERE slug = $1
         AND created_at >= NOW() - INTERVAL '${TTL_SECONDS} seconds'`,
      [slug],
    );

    const rows = result.rows || [];
    if (rows.length === 0) {
      return new Response(NOT_FOUND_HTML, {
        status: 404,
        headers: { "Content-Type": "text/html" },
      });
    }

    return new Response(null, {
      status: 302,
      headers: { Location: rows[0].url },
    });
  } catch (err) {
    console.error("Redirect lookup failed:", err);
    return new Response("Internal error", { status: 500 });
  }
}
