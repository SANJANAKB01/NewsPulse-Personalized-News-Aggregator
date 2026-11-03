import { useCallback, useEffect, useState } from "react";
import { Bookmark, SlidersHorizontal } from "lucide-react";
import { Link } from "react-router-dom";
import { newsApi } from "../api/endpoints";
import type { Article, CategoriesResponse } from "../types";
import ArticleCard from "../components/ArticleCard";
import CategoryFilter from "../components/CategoryFilter";
import { useAuth } from "../contexts/AuthContext";

const ALL_TOPICS = [
  "technology", "sports", "finance", "business", "travel",
  "entertainment", "health", "science", "politics", "world",
];

export default function Feed() {
  const { user } = useAuth();
  const [articles, setArticles] = useState<Article[]>([]);
  const [selectedTopics, setSelectedTopics] = useState<string[]>(user?.preferences || []);
  const [excludeRead, setExcludeRead] = useState(false);
  const [categoryData, setCategoryData] = useState<CategoriesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadFeed = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await newsApi.feed({
        limit: 30,
        preferences: selectedTopics,
        exclude_read: excludeRead,
      });
      setArticles(data.articles);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, [selectedTopics, excludeRead]);

  useEffect(() => {
    if (user && !selectedTopics.length) {
      setSelectedTopics(user.preferences);
    }
  }, [user, selectedTopics.length]);

  useEffect(() => {
    newsApi.categories().then(setCategoryData).catch(() => {});
  }, []);

  useEffect(() => {
    const t = setTimeout(loadFeed, 250);
    return () => clearTimeout(t);
  }, [loadFeed]);

  const toggleTopic = (topic: string) => {
    setSelectedTopics((prev) =>
      prev.includes(topic) ? prev.filter((t) => t !== topic) : [...prev, topic],
    );
  };

  const topicItems = (categoryData?.by_topic || []).map((d) => ({
    topic: d.topic!,
    count: d.count,
  }));

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold tracking-tight">For You</h1>
        <p className="mt-1 text-sm text-slate-500">
          {selectedTopics.length
            ? `Recommendations based on your interests: ${selectedTopics.join(", ")}`
            : "Pick your interests below to get personalized recommendations"}
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
        <aside className="space-y-4">
          <div className="card p-4">
            <div className="mb-2 flex items-center justify-between">
              <h3 className="text-sm font-semibold">Your topics</h3>
              <SlidersHorizontal size={14} className="text-slate-400" />
            </div>
            <div className="flex flex-wrap gap-1.5">
              {ALL_TOPICS.map((topic) => {
                const active = selectedTopics.includes(topic);
                return (
                  <button
                    key={topic}
                    onClick={() => toggleTopic(topic)}
                    className={`rounded-lg px-2.5 py-1 text-xs font-medium transition-colors ${
                      active
                        ? "bg-brand-600 text-white"
                        : "bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                    }`}
                  >
                    {topic}
                  </button>
                );
              })}
            </div>
            <button
              onClick={() => setSelectedTopics([])}
              className="mt-3 w-full text-xs text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
            >
              Reset topics
            </button>
          </div>

          {topicItems.length > 0 && (
            <CategoryFilter items={topicItems} title="Topic distribution" />
          )}

          {user && (
            <label className="card flex cursor-pointer items-center gap-2 p-3 text-sm">
              <input
                type="checkbox"
                checked={excludeRead}
                onChange={(e) => setExcludeRead(e.target.checked)}
                className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
              />
              Hide already-read articles
            </label>
          )}
        </aside>

        <div>
          {error && (
            <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-300">
              {error}
            </div>
          )}

          {loading ? (
            <div className="grid gap-4 sm:grid-cols-2">
              {[0, 1, 2, 3].map((i) => (
                <div key={i} className="card h-72 animate-pulse p-4">
                  <div className="h-40 rounded bg-slate-200 dark:bg-slate-800" />
                  <div className="mt-3 h-4 w-3/4 rounded bg-slate-200 dark:bg-slate-800" />
                  <div className="mt-2 h-3 w-full rounded bg-slate-200 dark:bg-slate-800" />
                </div>
              ))}
            </div>
          ) : articles.length ? (
            <div className="grid gap-4 sm:grid-cols-2">
              {articles.map((a) => <ArticleCard key={a.id} article={a} />)}
            </div>
          ) : (
            <div className="card flex h-64 flex-col items-center justify-center gap-2 text-center">
              <Bookmark size={32} className="text-slate-300" />
              <p className="text-sm text-slate-500">No recommendations yet.</p>
              {selectedTopics.length === 0 && (
                <Link to="/profile" className="text-sm font-medium text-brand-600 hover:underline">
                  Set your topics →
                </Link>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
