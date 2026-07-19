import Dashboard from "@/components/Dashboard";

const API_URL = process.env.API_URL_INTERNAL || "http://localhost:8000";

export default async function HomePage() {
  let initialItems: any[] = [];
  let initialStats: any = { total_items: 0, by_topic: {}, by_source: {} };
  let initialStatus: any = {
    last_run_at: null,
    items_fetched: 0,
    items_saved: 0,
    message: "Backend not connected yet.",
  };

  try {
    const [itemsRes, statsRes, statusRes] = await Promise.all([
      fetch(`${API_URL}/api/items?limit=12`, { next: { revalidate: 300 } }),
      fetch(`${API_URL}/api/stats`, { next: { revalidate: 300 } }),
      fetch(`${API_URL}/api/pipeline/status`, { next: { revalidate: 300 } }),
    ]);

    if (itemsRes.ok) initialItems = await itemsRes.json();
    if (statsRes.ok) initialStats = await statsRes.json();
    if (statusRes.ok) initialStatus = await statusRes.json();
  } catch {
    // Backend may not be up during first load.
  }

  return (
    <Dashboard initialItems={initialItems} initialStats={initialStats} initialStatus={initialStatus} />
  );
}
