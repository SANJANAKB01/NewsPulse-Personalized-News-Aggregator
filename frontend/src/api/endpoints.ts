import api, { setToken, clearToken } from "./client";
import type {
  Article,
  AuthResponse,
  CategoriesResponse,
  FeedResponse,
  NewsletterSubscriber,
  SearchResponse,
  SentimentResponse,
  StatsResponse,
  TrendingResponse,
  TopicsResponse,
} from "../types";

// ---- Auth ----------------------------------------------------------------
export const authApi = {
  register: async (email: string, username: string, password: string) => {
    const { data } = await api.post<AuthResponse>("/auth/register", { email, username, password });
    setToken(data.token);
    return data;
  },
  login: async (identifier: string, password: string) => {
    const { data } = await api.post<AuthResponse>("/auth/login", { identifier, password });
    setToken(data.token);
    return data;
  },
  me: async () => {
    const { data } = await api.get<{ user: { id: number; email: string; username: string; preferences: string[] } }>("/auth/me");
    return data.user;
  },
  updatePreferences: async (preferences: string[]) => {
    const { data } = await api.put<{ user: { id: number; email: string; username: string; preferences: string[] } }>("/auth/preferences", { preferences });
    return data.user;
  },
  logout: () => clearToken(),
};

// ---- News ----------------------------------------------------------------
export const newsApi = {
  feed: async (params: { limit?: number; preferences?: string[]; exclude_read?: boolean } = {}) => {
    const query = new URLSearchParams();
    if (params.limit) query.set("limit", String(params.limit));
    if (params.preferences && params.preferences.length) query.set("preferences", params.preferences.join(","));
    if (params.exclude_read) query.set("exclude_read", "1");
    const { data } = await api.get<FeedResponse>(`/news/feed?${query.toString()}`);
    return data;
  },
  search: async (params: Record<string, string | number | undefined>) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== "" && v !== null) query.set(k, String(v));
    });
    const { data } = await api.get<SearchResponse>(`/news/search?${query.toString()}`);
    return data;
  },
  getArticle: async (id: number) => {
    const { data } = await api.get<{ article: Article }>(`/news/article/${id}`);
    return data.article;
  },
  markRead: async (id: number) => {
    await api.post(`/news/article/${id}/read`);
  },
  share: async (id: number, platform: string) => {
    const { data } = await api.post<{ ok: boolean; share_count: number }>(`/news/article/${id}/share`, { platform });
    return data;
  },
  trending: async () => {
    const { data } = await api.get<TrendingResponse>("/news/trending");
    return data;
  },
  categories: async () => {
    const { data } = await api.get<CategoriesResponse>("/news/categories");
    return data;
  },
  sentiment: async () => {
    const { data } = await api.get<SentimentResponse>("/news/sentiment");
    return data;
  },
  breaking: async (limit = 10) => {
    const { data } = await api.get<{ articles: Article[]; count: number }>(`/news/breaking?limit=${limit}`);
    return data;
  },
  topics: async () => {
    const { data } = await api.get<TopicsResponse>("/news/topics");
    return data;
  },
  sources: async () => {
    const { data } = await api.get<{ sources: { source: string; name: string; count: number }[] }>("/news/sources");
    return data;
  },
  refresh: async () => {
    const { data } = await api.post<{ ok: boolean; message: string }>("/news/refresh");
    return data;
  },
  fetchHistorical: async (params: { from_date: string; to_date: string; query?: string; sources?: string[] }) => {
    const { data } = await api.post<{
      ok: boolean;
      fetched: number;
      inserted: number;
      skipped: number;
      sources: string[];
      from_date: string;
      to_date: string;
      query: string;
      message?: string;
    }>("/news/fetch-historical", params);
    return data;
  },
  stats: async () => {
    const { data } = await api.get<StatsResponse>("/news/stats");
    return data;
  },
};

// ---- Bookmarks -----------------------------------------------------------
export const bookmarksApi = {
  list: async () => {
    const { data } = await api.get<{ articles: Article[]; count: number }>("/news/bookmarks");
    return data;
  },
  ids: async () => {
    const { data } = await api.get<{ ids: number[] }>("/news/bookmarks/ids");
    return new Set(data.ids);
  },
  add: async (articleId: number) => {
    await api.post(`/news/bookmarks/${articleId}`);
  },
  remove: async (articleId: number) => {
    await api.delete(`/news/bookmarks/${articleId}`);
  },
  history: async () => {
    const { data } = await api.get<{ history: { article: Article; read_at: string }[]; count: number }>("/news/history");
    return data;
  },
};

// ---- Newsletter ----------------------------------------------------------
export const newsletterApi = {
  subscribe: async (email: string, frequency: string, topics: string[]) => {
    const { data } = await api.post<{ ok: boolean; subscriber: NewsletterSubscriber; confirm_token?: string }>("/newsletter/subscribe", { email, frequency, topics });
    return data;
  },
  unsubscribe: async (email: string) => {
    const { data } = await api.post<{ ok: boolean }>("/newsletter/unsubscribe", { email });
    return data;
  },
  list: async () => {
    const { data } = await api.get<{ subscribers: NewsletterSubscriber[]; count: number }>("/newsletter/subscribers");
    return data;
  },
};