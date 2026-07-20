import { DiscussionItem, PipelineStatus, ResearchItem, Stats } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://ai-research-backend-liv2.onrender.com";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`API error ${response.status} for ${path}`);
  }

  return response.json();
}

export function fetchItems(
  topic?: string,
  searchQuery?: string,
  customTopics?: string[],
  isFavorite?: boolean,
): Promise<ResearchItem[]> {
  const queryParams = new URLSearchParams();
  if (topic) queryParams.append("topic", topic);
  if (searchQuery) queryParams.append("search", searchQuery);
  if (customTopics && customTopics.length > 0) {
    customTopics.forEach((t) => queryParams.append("custom_topics", t));
  }
  if (isFavorite !== undefined) {
    queryParams.append("is_favorite", String(isFavorite));
  }
  const query = queryParams.toString();
  return request<ResearchItem[]>(`/api/items${query ? `?${query}` : ""}`);
}

export function fetchFavorites(): Promise<ResearchItem[]> {
  return request<ResearchItem[]>("/api/items?is_favorite=true&limit=200");
}

export function fetchTopics(): Promise<string[]> {
  return request<string[]>("/api/topics");
}

export function fetchStats(): Promise<Stats> {
  return request<Stats>("/api/stats");
}

export function fetchPipelineStatus(): Promise<PipelineStatus> {
  return request<PipelineStatus>("/api/pipeline/status");
}

export function runPipeline(): Promise<PipelineStatus> {
  return request<PipelineStatus>("/api/pipeline/run", { method: "POST" });
}

export function setFavorite(itemId: number, favorite: boolean): Promise<ResearchItem> {
  return request<ResearchItem>(`/api/items/${itemId}/favorite`, {
    method: "POST",
    body: JSON.stringify({ favorite }),
  });
}

export function fetchDiscussions(
  topic?: string,
  search?: string,
  sort?: string,
): Promise<DiscussionItem[]> {
  const params = new URLSearchParams();
  if (topic && topic !== "All") params.append("topic", topic);
  if (search) params.append("search", search);
  if (sort) params.append("sort", sort);
  const qs = params.toString();
  return request<DiscussionItem[]>(`/api/discussions${qs ? `?${qs}` : ""}`);
}

export function fetchDiscussionStatus(): Promise<{ last_run_at: string | null }> {
  return request("/api/discussions/status");
}

export function runDiscussionPipeline(): Promise<{
  items_fetched: number;
  items_saved: number;
  message: string;
}> {
  return request("/api/discussions/run", { method: "POST" });
}

export interface ChatResponse {
  answer: string;
  research: {
    type: string;
    title: string;
    summary: string;
    why: string;
    topics: string[];
    url: string;
    score: number;
    source: string;
  }[];
  discussions: {
    type: string;
    title: string;
    summary: string;
    url: string;
    score: number;
    source: string;
  }[];
}

export function sendChatMessage(question: string): Promise<ChatResponse> {
  return request<ChatResponse>("/api/chat", {
    method: "POST",
    body: JSON.stringify({ question }),
  });
}

