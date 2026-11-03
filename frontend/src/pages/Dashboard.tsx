import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Activity, BarChart3, FileText, TrendingUp } from "lucide-react";
import { newsApi } from "../api/endpoints";
import type { Article, CategoriesResponse, SentimentResponse, StatsResponse, TrendingResponse } from "../types";
import ArticleCard from "../components/ArticleCard";
import BreakingNewsBanner from "../components/BreakingNewsBanner";
import TrendingChart from "../components/TrendingChart";
import CategoryChart from "../components/CategoryChart";
import SentimentChart from "../components/SentimentChart";

export default function Dashboard() {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [trending, setTrending] = useState<TrendingResponse | null>(null);
  const [categories, setCategories] = useState<CategoriesResponse | null>(null);
  const [sentiment, setSentiment] = useState<SentimentResponse | null>(null);
  const [recent, setRecent] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      newsApi.stats().catch((e) => { console.warn(e); return null; }),
      newsApi.trending().catch((e) => { console.warn(e); return null; }),
      newsApi.categories().catch((e) => { console.warn(e); return null; }),
      newsApi.sentiment().catch((e) => { console.warn(e); return null; }),
      newsApi.search({ sort: "recent", page: 1, page_size: 6 }).catch((e) => { console.warn(e); return null; }),
    ])
      .then(([s, t, c, sm, sr]) => {
        if (s) setStats(s);
        if (t) setTrending(t);
        if (c) setCategories(c);
        if (sm) setSentiment(sm);
        if (sr) setRecent(sr.articles);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const handleRefresh = async () => {
    setLoading(true);
    try {
      await newsApi.refresh();
      window.location.reload();
    } catch (err) {
      setError((err as Error).message);
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6">
      <BreakingNewsBanner />

      <div className="mb-6 mt-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="mt-1 text-sm text-slate-500">
            Live news analytics across NewsAPI, Reddit &amp; GDELT
          </p>
        </div>
        <button onClick={handleRefresh} className="btn-secondary" disabled={loading}>
          <Activity size={16} /> Refresh feed
        </button>
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-300">
          {error}
        </div>
      )}

      {/* Stat cards */}
      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatCard
          icon={<FileText size={18} />}
          label="Total articles"
          value={stats?.total_articles ?? "—"}
          accent="text-brand-600"
        />
        <StatCard
          icon={<TrendingUp size={18} />}
          label="Last 24h"
          value={stats?.articles_last_24h ?? "—"}
          accent="text-emerald-600"
        />
        <StatCard
          icon={<BarChart3 size={18} />}
          label="Topics tracked"
          value={categories?.by_topic.length ?? "—"}
          accent="text-violet-600"
        />
        <StatCard
          icon={<Activity size={18} />}
          label="Breaking"
          value={stats?.breaking_articles ?? "—"}
          accent="text-rose-600"
        />
      </div>

      {/* Charts */}
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          {trending && <TrendingChart data={trending.trending} />}
        </div>
        <div>
          {categories && <CategoryChart data={categories} />}
        </div>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <h2 className="mb-3 text-lg font-semibold">Latest Articles</h2>
          {loading ? (
            <SkeletonGrid />
          ) : recent.length ? (
            <div className="grid gap-4 sm:grid-cols-2">
              {recent.map((a) => <ArticleCard key={a.id} article={a} />)}
            </div>
          ) : (
            <div className="card flex h-48 items-center justify-center text-sm text-slate-500">
              No articles yet. Run <code className="mx-1 rounded bg-slate-100 px-1 dark:bg-slate-800">python seed.py</code> to populate.
            </div>
          )}
        </div>
        <div>
          {sentiment && <SentimentChart data={sentiment} />}
        </div>
      </div>

      <div className="mt-8 text-center">
        <Link to="/feed" className="btn-primary">
          See personalized recommendations →
        </Link>
      </div>
    </div>
  );
}

function StatCard({ icon, label, value, accent }: { icon: React.ReactNode; label: string; value: React.ReactNode; accent: string }) {
  return (
    <div className="card p-4">
      <div className={`mb-2 inline-flex rounded-lg bg-slate-100 p-2 dark:bg-slate-800 ${accent}`}>
        {icon}
      </div>
      <div className="text-2xl font-bold">{value}</div>
      <div className="text-xs text-slate-500">{label}</div>
    </div>
  );
}

function SkeletonGrid() {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {[0, 1, 2, 3].map((i) => (
        <div key={i} className="card h-64 animate-pulse p-4">
          <div className="h-32 rounded bg-slate-200 dark:bg-slate-800" />
          <div className="mt-4 h-4 w-3/4 rounded bg-slate-200 dark:bg-slate-800" />
          <div className="mt-2 h-3 w-full rounded bg-slate-200 dark:bg-slate-800" />
          <div className="mt-2 h-3 w-5/6 rounded bg-slate-200 dark:bg-slate-800" />
        </div>
      ))}
    </div>
  );
}
