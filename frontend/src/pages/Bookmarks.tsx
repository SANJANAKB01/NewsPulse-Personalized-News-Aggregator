import { useEffect, useState } from "react";
import { Bookmark } from "lucide-react";
import { bookmarksApi } from "../api/endpoints";
import type { Article } from "../types";
import ArticleCard from "../components/ArticleCard";

export default function Bookmarks() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await bookmarksApi.list();
      setArticles(data.articles);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold tracking-tight">Saved Articles</h1>
        <p className="mt-1 text-sm text-slate-500">
          Articles you've bookmarked for later reading
        </p>
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-300">
          {error}
        </div>
      )}

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[0, 1, 2].map((i) => (
            <div key={i} className="card h-64 animate-pulse" />
          ))}
        </div>
      ) : articles.length ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {articles.map((a) => <ArticleCard key={a.id} article={a} bookmarked />)}
        </div>
      ) : (
        <div className="card flex h-64 flex-col items-center justify-center gap-2 text-center">
          <Bookmark size={32} className="text-slate-300" />
          <p className="text-sm text-slate-500">You haven't saved any articles yet.</p>
          <a href="/feed" className="text-sm font-medium text-brand-600 hover:underline">Browse articles →</a>
        </div>
      )}
    </div>
  );
}
