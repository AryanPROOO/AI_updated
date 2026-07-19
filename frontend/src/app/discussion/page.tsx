"use client";

import { useEffect, useState } from "react";
import DiscussionDashboard from "@/components/DiscussionDashboard";
import { fetchDiscussions, fetchDiscussionStatus } from "@/lib/api";

export default function DiscussionPage() {
  const [initialItems, setInitialItems] = useState<any[]>([]);
  const [initialStatus, setInitialStatus] = useState<{ last_run_at: string | null }>({ last_run_at: null });

  useEffect(() => {
    Promise.all([
      fetchDiscussions().catch(() => []),
      fetchDiscussionStatus().catch(() => ({ last_run_at: null })),
    ]).then(([items, status]) => {
      setInitialItems(items);
      setInitialStatus(status);
    });
  }, []);

  return (
    <DiscussionDashboard initialItems={initialItems} initialStatus={initialStatus} />
  );
}
