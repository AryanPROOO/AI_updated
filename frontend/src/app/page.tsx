"use client";

import { useEffect, useState } from "react";
import Dashboard from "@/components/Dashboard";
import { fetchItems, fetchStats, fetchPipelineStatus } from "@/lib/api";

export default function HomePage() {
  const [initialItems, setInitialItems] = useState<any[]>([]);
  const [initialStats, setInitialStats] = useState<any>({ total_items: 0, by_topic: {}, by_source: {} });
  const [initialStatus, setInitialStatus] = useState<any>({
    last_run_at: null,
    items_fetched: 0,
    items_saved: 0,
    message: "Backend not connected yet.",
  });

  useEffect(() => {
    Promise.all([
      fetchItems().catch(() => []),
      fetchStats().catch(() => ({ total_items: 0, by_topic: {}, by_source: {} })),
      fetchPipelineStatus().catch(() => ({
        last_run_at: null,
        items_fetched: 0,
        items_saved: 0,
        message: "Backend not connected yet.",
      })),
    ]).then(([items, stats, status]) => {
      setInitialItems(items);
      setInitialStats(stats);
      setInitialStatus(status);
    });
  }, []);

  return (
    <Dashboard initialItems={initialItems} initialStats={initialStats} initialStatus={initialStatus} />
  );
}
