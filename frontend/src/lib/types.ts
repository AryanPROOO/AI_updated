export type ResearchItem = {
  id: number;
  external_id: string;
  title: string;
  snippet: string | null;
  authors: string[] | null;
  source: string;
  bucket: string;
  published_at: string | null;
  topics: string[];
  summary: string | null;
  why_it_matters: string | null;
  paper_url: string | null;
  pdf_url: string | null;
  code_url: string | null;
  read_more_url: string | null;
  thumbnail_url: string | null;
  relevance_score: number;
  freshness_score: number;
  impact_score: number;
  total_score: number;
  is_favorite: boolean;
  created_at: string;
};

export type PipelineStatus = {
  last_run_at: string | null;
  items_fetched: number;
  items_saved: number;
  message: string;
};

export type Stats = {
  total_items: number;
  by_topic: Record<string, number>;
  by_source: Record<string, number>;
};

export type DiscussionItem = {
  id: number;
  title: string;
  content: string | null;
  source: string;
  source_url: string | null;
  thumbnail_url: string | null;
  author: string | null;
  score: number;
  num_comments: number;
  topics: string[];
  published_at: string | null;
  created_at: string;
};
