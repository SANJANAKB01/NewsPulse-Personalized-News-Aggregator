export interface Article {
  id: number;
  external_id?: string;
  source?: string;
  source_name?: string;
  title: string;
  description?: string;
  url: string;
  url_to_image?: string | null;
  author?: string | null;
  category?: string;
  topic?: string;
  sentiment_score?: number;
  sentiment_label?: "positive" | "negative" | "neutral" | string;
  reading_time_min?: number;
  published_at?: string | null;
  fetched_at?: string | null;
  is_breaking?: boolean;
  share_count?: number;
  saved_at?: string;
}

export interface User {
  id: number;
  email: string;
  username: string;
  preferences: string[];
  is_admin?: boolean;
  created_at?: string;
}

export interface AuthResponse {
  token: string;
  user: User;
}

export interface FeedResponse {
  articles: Article[];
  preferences_used: string[];
  count: number;
}

export interface SearchResponse {
  articles: Article[];
  page: number;
  page_size: number;
  total: number;
  pages: number;
}

export interface TrendingItem {
  topic: string;
  count: number;
}

export interface TrendingResponse {
  trending: TrendingItem[];
  since: string;
}

export interface CategoryItem {
  topic?: string;
  source?: string;
  name?: string;
  count: number;
}

export interface CategoriesResponse {
  by_topic: CategoryItem[];
  by_source: CategoryItem[];
}

export interface SentimentResponse {
  distribution: { label: string; count: number }[];
  average_score: number;
}

export interface StatsResponse {
  total_articles: number;
  breaking_articles: number;
  articles_last_24h: number;
}

export interface TopicsResponse {
  topics: string[];
  keywords: Record<string, string[]>;
}

export interface NewsletterSubscriber {
  id: number;
  email: string;
  frequency: string;
  topics: string[];
  confirmed: boolean;
  created_at?: string;
}
