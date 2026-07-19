import { ResearchItem } from "@/lib/types";
import { setFavorite } from "@/lib/api";
import { useState } from "react";

function formatDate(value: string | null) {
  if (!value) return "Unknown date";
  return new Date(value).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function CardImage({ item, gradient }: { item: ResearchItem; gradient: string }) {
  const [imgError, setImgError] = useState(false);
  const initials = item.title
    .split(" ")
    .slice(0, 3)
    .map((w) => w[0])
    .join("")
    .toUpperCase();

  if (item.thumbnail_url && !imgError) {
    return (
      <div className="relative h-48 overflow-hidden rounded-t-2xl">
        <img
          src={item.thumbnail_url}
          alt={item.title}
          className="h-full w-full object-cover"
          loading="lazy"
          onError={() => setImgError(true)}
        />
      </div>
    );
  }

  return (
    <div
      className="relative flex h-48 items-end rounded-t-2xl p-5"
      style={{ background: gradient }}
    >
      <span className="text-4xl font-bold text-white/10">{initials}</span>
    </div>
  );
}

function isTopPick(score: number): boolean {
  return score >= 0.75;
}

export default function ResearchCard({ item, gradient }: { item: ResearchItem; gradient: string }) {
  const [isFavorite, setIsFavorite] = useState(item.is_favorite);
  const topPick = isTopPick(item.total_score);

  const handleFavoriteClick = async () => {
    try {
      const updatedItem = await setFavorite(item.id, !isFavorite);
      setIsFavorite(updatedItem.is_favorite);
    } catch (error) {
      console.error("Failed to update favorite status:", error);
    }
  };

  return (
    <article className={`card-hover group overflow-hidden rounded-2xl border ${topPick ? "border-amber-400 ring-1 ring-amber-400" : "border-gray-200"} bg-white shadow-sm`}>
      <div className="relative">
        <CardImage item={item} gradient={gradient} />
        {topPick && (
          <span className="absolute left-3 top-3 rounded-full bg-amber-400 px-3 py-1 text-xs font-bold text-black shadow">
            🔥 Top Pick
          </span>
        )}
        <button
          onClick={handleFavoriteClick}
          className={`absolute right-3 top-3 rounded-full p-2 text-lg transition backdrop-blur-sm ${
            isFavorite
              ? "text-yellow-400"
              : "text-white/60 hover:text-yellow-300"
          }`}
          title={isFavorite ? "Remove from favorites" : "Add to favorites"}
        >
          {isFavorite ? "★" : "☆"}
        </button>
      </div>

      <div className="p-5">
        <div className="mb-3 flex flex-wrap items-center gap-2">
          {item.topics.slice(0, 2).map((topic) => (
            <span
              key={topic}
              className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-700"
            >
              {topic}
            </span>
          ))}
          <span className="text-xs text-gray-400">{formatDate(item.published_at)}</span>
        </div>

        <h3 className="text-base font-semibold leading-snug text-black line-clamp-2">
          {item.title}
        </h3>

        {item.summary && (
          <p className="mt-2 text-sm leading-relaxed text-gray-600">
            {item.summary}
          </p>
        )}

        {item.why_it_matters && (
          <div className="mt-2 rounded-lg bg-blue-50 px-3 py-2">
            <p className="text-xs font-semibold text-blue-700">Why it matters</p>
            <p className="mt-0.5 text-xs leading-relaxed text-blue-900">
              {item.why_it_matters}
            </p>
          </div>
        )}

        {item.authors && item.authors.length > 0 && (
          <p className="mt-2 text-xs text-gray-400 truncate">
            {item.authors.slice(0, 3).join(", ")}
          </p>
        )}

        <div className="mt-4 flex items-center justify-between">
          <div className="flex gap-2">
            {item.pdf_url && (
              <a
                href={item.pdf_url}
                target="_blank"
                rel="noreferrer"
                className="rounded-full bg-black px-4 py-2 text-xs font-medium text-white transition hover:bg-gray-800"
              >
                PDF
              </a>
            )}
            {item.read_more_url && (
              <a
                href={item.read_more_url}
                target="_blank"
                rel="noreferrer"
                className="rounded-full border border-gray-300 px-4 py-2 text-xs font-medium text-gray-700 transition hover:bg-gray-100"
              >
                Read
              </a>
            )}
          </div>
          <span className="text-xs text-gray-400">Score: {item.total_score.toFixed(1)}</span>
        </div>
      </div>
    </article>
  );
}
