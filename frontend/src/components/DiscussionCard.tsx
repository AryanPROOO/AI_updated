import { DiscussionItem } from "@/lib/types";

function decodeEntities(text: string | null): string {
  if (!text) return "";
  const textarea = document.createElement("textarea");
  textarea.innerHTML = text;
  return textarea.value;
}

function formatDate(value: string | null) {
  if (!value) return "";
  return new Date(value).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function timeAgo(value: string | null) {
  if (!value) return "";
  const diff = Date.now() - new Date(value).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

const sourceColors: Record<string, string> = {
  reddit: "bg-orange-100 text-orange-700",
  twitter: "bg-blue-100 text-blue-700",
};

const HOT_TOPICS = new Set(["LLM", "Agents", "Computer Vision"]);

function isHotTopic(item: DiscussionItem): boolean {
  return (item.topics || []).some((t) => HOT_TOPICS.has(t));
}

export default function DiscussionCard({ item }: { item: DiscussionItem }) {
  const title = decodeEntities(item.title);
  const content = decodeEntities(item.content);
  const author = decodeEntities(item.author);
  const hot = isHotTopic(item);

  return (
    <article className={`card-hover overflow-hidden rounded-2xl border ${hot ? "border-blue-400 ring-1 ring-blue-400" : "border-gray-200"} bg-white shadow-sm`}>
      <div className="p-5">
      <div className="mb-3 flex items-start justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className={`rounded-full px-3 py-1 text-xs font-medium ${sourceColors[item.source] || "bg-gray-100 text-gray-700"}`}>
            {item.source === "reddit" ? "r/" : ""}{item.source}
          </span>
          {hot && (
            <span className="rounded-full bg-blue-500 px-3 py-1 text-xs font-bold text-white shadow">
              📈 Trending
            </span>
          )}
          {item.topics.slice(0, 2).map((t) => (
              <span key={t} className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-600">
                {t}
              </span>
            ))}
            <span className="text-xs text-gray-400">{timeAgo(item.published_at)}</span>
          </div>
          <div className="flex items-center gap-3 text-xs text-gray-400 shrink-0">
            <span title="Score" className="flex items-center gap-1">
              <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16m-7 6h7" />
              </svg>
              {item.score}
            </span>
            <span title="Comments" className="flex items-center gap-1">
              <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              {item.num_comments}
            </span>
          </div>
        </div>

        <h3 className="text-base font-semibold leading-snug text-black">
          <a href={item.source_url || "#"} target="_blank" rel="noreferrer" className="hover:underline">
            {title}
          </a>
        </h3>

        {content && (
          <p className="mt-2 text-sm leading-relaxed text-gray-600 line-clamp-3">
            {content}
          </p>
        )}

        <div className="mt-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            {author && (
              <span className="text-xs text-gray-400">by {author}</span>
            )}
          </div>
          {item.source_url && (
            <a
              href={item.source_url}
              target="_blank"
              rel="noreferrer"
              className="rounded-full border border-gray-300 px-4 py-1.5 text-xs font-medium text-gray-700 transition hover:bg-gray-100"
            >
              Open {item.source === "reddit" ? "Reddit" : "X"}
            </a>
          )}
        </div>
      </div>
    </article>
  );
}
