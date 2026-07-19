"use client";

import { useMemo, useState, useTransition, useCallback, useEffect } from "react";

import ResearchCard from "@/components/ResearchCard";
import { fetchItems, runPipeline } from "@/lib/api";
import { PipelineStatus, ResearchItem, Stats } from "@/lib/types";

const TOPICS = ["All", "LLM", "Agents", "Edge AI", "Robotics", "Computer Vision", "Reinforcement Learning"];

type DashboardProps = {
  initialItems: ResearchItem[];
  initialStats: Stats;
  initialStatus: PipelineStatus;
};

const sourceGradients: Record<string, string> = {
  arxiv: "linear-gradient(135deg, #1f2937, #374151)",
  huggingface: "linear-gradient(135deg, #111827, #1f2937)",
  github_trending: "linear-gradient(135deg, #374151, #4b5563)",
  openalex: "linear-gradient(135deg, #111827, #374151)",
};

function getSourceGradient(source: string) {
  return sourceGradients[source] || "linear-gradient(135deg, #1f2937, #374151)";
}

export default function Dashboard({
  initialItems,
  initialStats,
  initialStatus,
}: DashboardProps) {
  const [items, setItems] = useState(initialItems);
  const [stats, setStats] = useState(initialStats);
  const [status, setStatus] = useState(initialStatus);
  const [activeTopic, setActiveTopic] = useState("All");
  const [searchQuery, setSearchQuery] = useState("");
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();
  const [heroImgError, setHeroImgError] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // Auto-refresh: check for new items every 5 minutes
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const nextItems = await fetchItems(
          activeTopic === "All" ? undefined : activeTopic,
          searchQuery || undefined,
          undefined,
          showFavoritesOnly || undefined,
        );
        if (nextItems.length !== items.length) {
          setItems(nextItems);
          setLastUpdated(new Date());
        }
      } catch {
        // Silently fail on auto-refresh
      }
    }, 5 * 60 * 1000); // 5 minutes

    return () => clearInterval(interval);
  }, [activeTopic, searchQuery, showFavoritesOnly, items.length]);

  const sortedAndFilteredItems = useMemo(() => {
    let processed = [...items];

    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      processed = processed.filter(
        (item) =>
          item.title.toLowerCase().includes(q) ||
          (item.snippet && item.snippet.toLowerCase().includes(q)) ||
          (item.summary && item.summary.toLowerCase().includes(q))
      );
    }

    if (activeTopic !== "All") {
      processed = processed.filter((item) => item.topics.includes(activeTopic));
    }

    if (showFavoritesOnly) {
      processed = processed.filter((item) => item.is_favorite);
    }

    processed.sort((a, b) => b.total_score - a.total_score);

    return processed;
  }, [items, activeTopic, searchQuery, showFavoritesOnly]);

  const featured = sortedAndFilteredItems[0];

  // Reset hero image error when featured item changes
  const featuredId = featured?.id;
  useMemo(() => {
    setHeroImgError(false);
  }, [featuredId]);

  const refreshAll = (
    topic = activeTopic,
    query = searchQuery,
    favoritesOnly = showFavoritesOnly,
  ) => {
    startTransition(async () => {
      try {
        setError(null);
        const nextItems = await fetchItems(
          topic === "All" ? undefined : topic,
          query || undefined,
          undefined,
          favoritesOnly || undefined,
        );
        setItems(nextItems);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to refresh items");
      }
    });
  };

  const handleTopicChange = (topic: string) => {
    setActiveTopic(topic);
    refreshAll(topic, searchQuery, showFavoritesOnly);
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
    refreshAll(activeTopic, e.target.value, showFavoritesOnly);
  };

  const handleToggleFavorites = () => {
    const next = !showFavoritesOnly;
    setShowFavoritesOnly(next);
    refreshAll(activeTopic, searchQuery, next);
  };

  const handleRunPipeline = () => {
    startTransition(async () => {
      try {
        setError(null);
        const nextStatus = await runPipeline();
        setStatus(nextStatus);
        refreshAll(activeTopic, searchQuery, showFavoritesOnly);
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
              <span className="rounded-md bg-black px-3 py-1.5 text-xs font-medium text-white">
                Research
              </span>
              <a
                href="/discussion"
                className="rounded-md px-3 py-1.5 text-xs font-medium text-gray-500 transition hover:bg-gray-100"
              >
                AI Discussion
              </a>
            </div>
          </div>

          <div className="hidden flex-1 justify-center px-8 sm:flex">
            <div className="relative w-full max-w-md">
              <svg className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                type="text"
                placeholder="Search research papers..."
                value={searchQuery}
                onChange={handleSearchChange}
                className="w-full rounded-full border border-gray-300 bg-white py-2 pl-10 pr-4 text-sm text-black placeholder-gray-400 focus:border-black focus:outline-none focus:ring-2 focus:ring-black/10"
              />
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleToggleFavorites}
              className={`rounded-full border px-4 py-2 text-sm font-medium transition ${
                showFavoritesOnly
                  ? "border-black bg-black text-white"
                  : "border-gray-300 text-gray-700 hover:bg-gray-100"
              }`}
            >
              {showFavoritesOnly ? "★ Favorites" : "☆ Favorites"}
            </button>
            <button
              onClick={handleRunPipeline}
              disabled={isPending}
              className="rounded-full bg-black px-5 py-2 text-sm font-medium text-white transition hover:bg-gray-800 disabled:opacity-60"
            >
              {isPending ? "Running..." : "Fetch Updates"}
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
              placeholder="Search research papers..."
              value={searchQuery}
              onChange={handleSearchChange}
              className="w-full rounded-full border border-gray-300 bg-white py-2 pl-10 pr-4 text-sm text-black placeholder-gray-400 focus:border-black focus:outline-none focus:ring-2 focus:ring-black/10"
            />
          </div>
        </div>
      </nav>

      {/* Hero Section with Thumbnail */}
      <section className="mx-4 mt-6 overflow-hidden rounded-3xl sm:mx-6 lg:mx-8">
        {featured ? (
          <div className="relative flex min-h-[320px] items-end sm:min-h-[380px] md:min-h-[420px]">
            {featured.thumbnail_url && !heroImgError ? (
              <img
                src={featured.thumbnail_url}
                alt={featured.title}
                className="absolute inset-0 h-full w-full object-cover"
                onError={() => setHeroImgError(true)}
              />
            ) : (
              <div className="absolute inset-0 bg-gray-900" />
            )}
            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/50 to-black/30" />
            <div className="relative z-10 w-full px-6 py-8 sm:px-10 sm:py-12 md:px-16 md:py-16">
              <div className="max-w-3xl">
                <span className="inline-flex items-center gap-1.5 rounded-full bg-red-500 px-3 py-1 text-xs font-semibold text-white">
                  <span className="h-1.5 w-1.5 rounded-full bg-white animate-pulse" />
                  LIVE UPDATES
                </span>
                <h1 className="mt-4 text-2xl font-bold leading-tight text-white sm:text-3xl md:text-4xl lg:text-5xl">
                  {featured.title}
                </h1>
                <p className="mt-3 max-w-2xl text-sm leading-relaxed text-gray-200 sm:text-base">
                  {featured.summary || featured.snippet || ""}
                </p>
                {featured.why_it_matters && (
                  <p className="mt-2 max-w-2xl text-sm leading-relaxed text-gray-300">
                    <span className="font-semibold text-white">Why it matters:</span>{" "}
                    {featured.why_it_matters}
                  </p>
                )}
                <div className="mt-5 flex flex-wrap gap-3">
                  <a
                    href={featured.pdf_url || featured.read_more_url || "#"}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-2 rounded-full bg-white px-6 py-3 text-sm font-semibold text-black transition hover:bg-gray-200"
                  >
                    Read Analysis
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                    </svg>
                  </a>
                  <button
                    onClick={handleRunPipeline}
                    disabled={isPending}
                    className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-6 py-3 text-sm font-medium text-white backdrop-blur-sm transition hover:bg-white/20"
                  >
                    {isPending ? "Refreshing..." : "Explore More"}
                  </button>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="relative flex min-h-[280px] items-end bg-gray-900 sm:min-h-[320px]">
            <div className="w-full px-6 py-10 sm:px-10 sm:py-14 md:px-16 md:py-18">
              <span className="inline-flex items-center gap-1.5 rounded-full bg-red-500 px-3 py-1 text-xs font-semibold text-white">
                <span className="h-1.5 w-1.5 rounded-full bg-white animate-pulse" />
                LIVE UPDATES
              </span>
              <h1 className="mt-4 text-2xl font-bold leading-tight text-white sm:text-3xl md:text-4xl">
                Discover Latest AI Research
              </h1>
              <p className="mt-3 max-w-2xl text-sm text-gray-300 sm:text-base">
                Stay ahead with daily AI research papers from arXiv, Hugging Face, and GitHub.
              </p>
              <div className="mt-5 flex flex-wrap gap-3">
                <button
                  onClick={handleRunPipeline}
                  disabled={isPending}
                  className="inline-flex items-center gap-2 rounded-full bg-white px-6 py-3 text-sm font-semibold text-black transition hover:bg-gray-200"
                >
                  {isPending ? "Loading..." : "Fetch Latest Papers"}
                </button>
              </div>
            </div>
          </div>
        )}
      </section>

      {/* Error */}
      {error && (
        <div className="mx-4 mt-6 rounded-xl border border-gray-300 bg-gray-50 px-4 py-3 text-sm text-black sm:mx-6 lg:mx-8">
          {error}
        </div>
      )}

      {/* Status message */}
      {status.message && (
        <p className="mx-4 mt-6 text-sm text-gray-500 sm:mx-6 lg:mx-8">{status.message}</p>
      )}

      {/* Auto-refresh indicator */}
      <div className="mx-4 mt-3 flex items-center gap-2 text-xs text-gray-400 sm:mx-6 lg:mx-8">
        <span className="h-1.5 w-1.5 rounded-full bg-green-500 animate-pulse" />
        Auto-refreshing every 5 minutes
        {lastUpdated && (
          <span>(last: {lastUpdated.toLocaleTimeString()})</span>
        )}
      </div>

      {/* Topic Filters */}
      <section className="mx-4 mt-8 flex flex-wrap gap-2 sm:mx-6 lg:mx-8">
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

      {/* Research Cards Grid */}
      <section className="mx-4 mt-8 grid gap-6 pb-12 sm:mx-6 lg:mx-8 lg:grid-cols-3">
        {sortedAndFilteredItems.length === 0 ? (
          <div className="col-span-full rounded-2xl border border-dashed border-gray-300 p-12 text-center text-gray-500">
            No papers found. Click &ldquo;Fetch Updates&rdquo; to load the latest research.
          </div>
        ) : (
          sortedAndFilteredItems.slice(featured ? 1 : 0).map((item) => (
            <ResearchCard key={item.id} item={item} gradient={getSourceGradient(item.source)} />
          ))
        )}
      </section>
    </div>
  );
}
