// Minimal Node.js (v18+) client for the ML REST API.  Usage: node client.js
const BASE = process.env.API_URL || "http://127.0.0.1:8000";

async function main() {
  const body = { route_id: "R01", departure_hour: 9, day_of_week: 0, weather: "Rain" };
  const res = await fetch(`${BASE}/predict/trip`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  });
  console.log("Trip prediction:", await res.json());
  const f = await (await fetch(`${BASE}/forecast?days=3`)).json();
  console.log("3-day forecast:", f);
}
main().catch((e) => console.error("Is the API running? ->", e.message));
