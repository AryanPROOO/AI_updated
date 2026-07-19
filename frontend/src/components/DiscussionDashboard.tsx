"use client";

import { useMemo, useState, useTransition } from "react";

import DiscussionCard from "@/components/DiscussionCard";
import { fetchDiscussions, runDiscussionPipeline } from "@/lib/api";
import { DiscussionItem } from "@/lib/types";

const TOPICS = ["All", "LLM", "Agents", "Edge AI", "Robotics", "Computer Vision", "Reinforcement Learning", "General AI"];

type Props = {
  initialItems: DiscussionItem[];
  initialStatus: { last_run_at: string | null };
};

export default function DiscussionDashboard({ initialItems, initialStatus }: Props) {
  const [items, setItems] = useState(initialItems);
  const [status, setStatus] = useState(initialStatus);
  const [activeTopic, setActiveTopic] = useState("All");
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState("comments");
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const filtered = useMemo(() => {
    let processed = [...items];

    if (activeTopic !== "All") {
      processed = processed.filter((item) => item.topics.includes(activeTopic));
    }

    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      processed = processed.filter(
        (item) =>
          item.title.toLowerCase().includes(q) ||
          (item.content && item.content.toLowerCase().includes(q))
      );
    }

    return processed;
  }, [items, activeTopic, searchQuery]);

  const refreshAll = (topic = activeTopic, query = searchQuery) => {
    startTransition(async () => {
      try {
        setError(null);
        const next = await fetchDiscussions(
          topic === "All" ? undefined : topic,
          query || undefined,
          sortBy,
        );
        setItems(next);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to refresh");
      }
    });
  };

  const handleTopicChange = (topic: string) => {
    setActiveTopic(topic);
    refreshAll(topic, searchQuery);
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
    refreshAll(activeTopic, e.target.value);
  };

  const handleSortChange = (sort: string) => {
    setSortBy(sort);
    startTransition(async () => {
      try {
        const next = await fetchDiscussions(
          activeTopic === "All" ? undefined : activeTopic,
          searchQuery || undefined,
          sort,
        );
        setItems(next);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to sort");
      }
    });
  };

  const handleFetch = () => {
    startTransition(async () => {
      try {
        setError(null);
        const result = await runDiscussionPipeline();
        setStatus({ last_run_at: new Date().toISOString() });
        const next = await fetchDiscussions(
          activeTopic === "All" ? undefined : activeTopic,
          searchQuery || undefined,
          sortBy,
        );
        setItems(next);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Pipeline run failed");
      }
    });
  };

  return (
    <div className="min-h-screen bg-white">
      {/* Top Navbar */}
      <nav className="sticky top-0 z-50 border-b border-gray-200 bg-white/80 backdrop-blur-lg">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
          <div className="flex items-center gap-3">
            <img src="/logo.png" alt="AI Research Agent" className="h-8 w-auto" />
            <div className="ml-2 flex gap-1 rounded-lg border border-gray-200 p-0.5">
              <a
                href="/"
                className="rounded-md px-3 py-1.5 text-xs font-medium text-gray-500 transition hover:bg-gray-100"
              >
                Research
              </a>
              <span className="rounded-md bg-black px-3 py-1.5 text-xs font-medium text-white">
                AI Discussion
              </span>
            </div>
          </div>

          <div className="hidden flex-1 justify-center px-8 sm:flex">
            <div className="relative w-full max-w-md">
              <svg className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                type="text"
                placeholder="Search discussions..."
                value={searchQuery}
                onChange={handleSearchChange}
                className="w-full rounded-full border border-gray-300 bg-white py-2 pl-10 pr-4 text-sm text-black placeholder-gray-400 focus:border-black focus:outline-none focus:ring-2 focus:ring-black/10"
              />
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1.5 rounded-full bg-red-500 px-3 py-1.5 text-xs font-semibold text-white">
              <span className="h-1.5 w-1.5 rounded-full bg-white animate-pulse" />
              LIVE
            </span>
            <button
              onClick={handleFetch}
              disabled={isPending}
              className="rounded-full bg-black px-5 py-2 text-sm font-medium text-white transition hover:bg-gray-800 disabled:opacity-60"
            >
              {isPending ? "Fetching..." : "Fetch Discussions"}
            </button>
            <div className="h-9 w-9 rounded-full bg-gray-300" />
          </div>
        </div>

        {/* Mobile search */}
        <div className="border-t border-gray-200 px-4 pb-3 sm:hidden">
          <div className="relative mt-3">
            <svg className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              placeholder="Search discussions..."
              value={searchQuery}
              onChange={handleSearchChange}
              className="w-full rounded-full border border-gray-300 bg-white py-2 pl-10 pr-4 text-sm text-black placeholder-gray-400 focus:border-black focus:outline-none focus:ring-2 focus:ring-black/10"
            />
          </div>
        </div>
      </nav>

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-black sm:text-3xl">AI Discussions</h1>
            <p className="mt-1 text-sm text-gray-500">
              Trending conversations from Reddit {status.last_run_at ? `(last fetched: ${new Date(status.last_run_at).toLocaleString()})` : ""}
            </p>
          </div>
          <div className="flex gap-2">
            {["comments", "score", "new"].map((s) => (
              <button
                key={s}
                onClick={() => handleSortChange(s)}
                className={`rounded-full px-4 py-2 text-sm font-medium transition ${
                  sortBy === s
                    ? "bg-black text-white"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                {s === "comments" ? "Most Discussed" : s === "score" ? "Top Rated" : "Newest"}
              </button>
            ))}
          </div>
        </div>

        {/* Topic Filters */}
        <section className="mb-6 flex flex-wrap gap-2">
          {TOPICS.map((topic) => (
            <button
              key={topic}
              onClick={() => handleTopicChange(topic)}
              className={`rounded-full px-4 py-2 text-sm font-medium transition ${
                activeTopic === topic
                  ? "bg-black text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              {topic}
            </button>
          ))}
        </section>

        {/* Error */}
        {error && (
          <div className="mb-6 rounded-xl border border-gray-300 bg-gray-50 px-4 py-3 text-sm text-black">
            {error}
          </div>
        )}

        {/* Discussion Cards */}
        <section className="grid gap-5">
          {filtered.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-gray-300 p-12 text-center text-gray-500">
              No discussions found. Click &ldquo;Fetch Discussions&rdquo; to load the latest from Reddit.
            </div>
          ) : (
            filtered.map((item) => (
              <DiscussionCard key={item.id} item={item} />
            ))
          )}
        </section>
      </main>
    </div>
  );
}
