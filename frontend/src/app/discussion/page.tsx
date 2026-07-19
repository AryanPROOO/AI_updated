import DiscussionDashboard from "@/components/DiscussionDashboard";

const API_URL = process.env.API_URL_INTERNAL || "http://localhost:8000";

export default async function DiscussionPage() {
  let initialItems: any[] = [];
  let initialStatus: { last_run_at: string | null } = { last_run_at: null };

  try {
    const [discussionsRes, statusRes] = await Promise.all([
      fetch(`${API_URL}/api/discussions?limit=20`, { next: { revalidate: 300 } }),
      fetch(`${API_URL}/api/discussions/status`, { next: { revalidate: 300 } }),
    ]);

    if (discussionsRes.ok) initialItems = await discussionsRes.json();
    if (statusRes.ok) initialStatus = await statusRes.json();
  } catch {
    // Backend may not be up during first load.
  }

  return (
    <DiscussionDashboard initialItems={initialItems} initialStatus={initialStatus} />
  );
}
