import { useEffect, useState } from "react";
import { CalendarClock, Filter, Loader2 } from "lucide-react";
import { newsApi } from "../api/endpoints";
import { useAuth } from "../contexts/AuthContext";
import type { Article, SearchResponse, TopicsResponse } from "../types";
import ArticleCard from "../components/ArticleCard";
import SearchBar from "../components/SearchBar";

const SOURCES = ["newsapi", "reddit", "gdelt", "guardian", "nyt", "hackernews", "rss", "newsdata", "gnews"];
const SENTIMENTS = ["positive", "neutral", "negative"];
const SORTS = [
  { value: "recent", label: "Most recent" },
  { value: "popular", label: "Most shared" },
  { value: "sentiment_pos", label: "Most positive" },
  { value: "sentiment_neg", label: "Most negative" },
];

const HISTORICAL_SOURCES = [
  { value: "guardian", label: "The Guardian (since 1999)" },
  { value: "nyt", label: "New York Times (since 1851)" },
];

export default function Search() {
  const { user } = useAuth();
  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState({
    topic: "",
    source: "",
    sentiment: "",
    from: "",
    to: "",
    sort: "recent",
  });
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [topics, setTopics] = useState<TopicsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [histFrom, setHistFrom] = useState("");
  const [histTo, setHistTo] = useState("");
  const [histQuery, setHistQuery] = useState("");
  const [histSources, setHistSources] = useState<string[]>(["guardian"]);
  const [histLoading, setHistLoading] = useState(false);
  const [histResult, setHistResult] = useState("");
  const [page, setPage] = useState(1);

  useEffect(() => {
    newsApi.topics().then(setTopics).catch(() => {});
  }, []);

  const toggleHistSource = (src: string) => {
    setHistSources((prev) => (prev.includes(src) ? prev.filter((s) => s !== src) : [...prev, src]));
  };

  const fetchHistorical = async () => {
    if (!user) {
      setHistResult("Please sign in to fetch historical news.");
      return;
    }
    if (!histFrom || !histTo) {
      setHistResult("Pick both a start and end date.");
      return;
    }
    if (!histSources.length) {
      setHistResult("Select at least one source.");
      return;
    }
    setHistLoading(true);
    setHistResult("Fetching historical articles... this can take 30-60 seconds.");
    try {
      const res = await newsApi.fetchHistorical({
        from_date: histFrom,
        to_date: histTo,
        query: histQuery || "news",
        sources: histSources,
      });
      setHistResult(`Fetched ${res.fetched} articles, inserted ${res.inserted} new, skipped ${res.skipped} duplicates.`);
      runSearch(1);
    } catch (err) {
      setHistResult(`Error: ${(err as Error).message}`);
    } finally {
      setHistLoading(false);
    }
  };

  const runSearch = async (p: number = 1) => {
    setLoading(true);
    setError("");
    try {
      const data = await newsApi.search({
        q: query || undefined,
        topic: filters.topic || undefined,
        source: filters.source || undefined,
        sentiment: filters.sentiment || undefined,
        from: filters.from || undefined,
        to: filters.to || undefined,
        sort: filters.sort,
        page: p,
        page_size: 20,
      });
      setResults(data);
      setPage(p);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const t = setTimeout(() => runSearch(1), 350);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, filters]);

  const updateFilter = (key: keyof typeof filters, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const articles: Article[] = results?.articles || [];

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold tracking-tight">Search &amp; Filter</h1>
        <p className="mt-1 text-sm text-slate-500">Full-text search across all sources with filters</p>
      </div>

      <div className="mb-4">
        <SearchBar onSearch={setQuery} initialValue={query} className="w-full" />
      </div>

      <div className="mb-6 card p-4">
        <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-700 dark:text-slate-300">
          <Filter size={16} /> Filters
        </div>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-6">
          <Select label="Topic" value={filters.topic} onChange={(v) => updateFilter("topic", v)}
            options={[{ value: "", label: "All topics" }].concat((topics?.topics || []).map((t) => ({ value: t, label: t })))} />
          <Select label="Source" value={filters.source} onChange={(v) => updateFilter("source", v)}
            options={[{ value: "", label: "All sources" }].concat(SOURCES.map((s) => ({ value: s, label: s })))} />
          <Select label="Sentiment" value={filters.sentiment} onChange={(v) => updateFilter("sentiment", v)}
            options={[{ value: "", label: "Any sentiment" }].concat(SENTIMENTS.map((s) => ({ value: s, label: s })))} />
          <Select label="Sort" value={filters.sort} onChange={(v) => updateFilter("sort", v)} options={SORTS} />
          <div>
            <label className="label">From date</label>
            <input type="date" value={filters.from} onChange={(e) => updateFilter("from", e.target.value)} className="input" />
          </div>
          <div>
            <label className="label">To date</label>
            <input type="date" value={filters.to} onChange={(e) => updateFilter("to", e.target.value)} className="input" />
          </div>
        </div>
      </div>

      <div className="mb-6 card border-l-4 border-l-brand-500 p-4">
        <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-700 dark:text-slate-300">
          <CalendarClock size={16} className="text-brand-500" />
          Fetch Historical News
          <span className="rounded-full bg-brand-50 px-2 py-0.5 text-xs font-normal text-brand-700 dark:bg-brand-900/30 dark:text-brand-300">Pull articles from any year</span>
        </div>
        {!user && (
          <p className="mb-3 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-700 dark:bg-amber-950/40 dark:text-amber-300">Sign in to fetch historical news into your database.</p>
        )}
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <label className="label">Start date</label>
            <input type="date" value={histFrom} onChange={(e) => setHistFrom(e.target.value)} className="input" />
          </div>
          <div>
            <label className="label">End date</label>
            <input type="date" value={histTo} onChange={(e) => setHistTo(e.target.value)} className="input" />
          </div>
          <div className="lg:col-span-2">
            <label className="label">Search query (optional)</label>
            <input type="text" value={histQuery} onChange={(e) => setHistQuery(e.target.value)} placeholder='e.g. "climate change" or "election"' className="input" />
          </div>
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <span className="text-xs text-slate-500">Sources:</span>
          {HISTORICAL_SOURCES.map((s) => {
            const active = histSources.includes(s.value);
            return (
              <button key={s.value} onClick={() => toggleHistSource(s.value)}
                className={`rounded-lg border px-2.5 py-1 text-xs font-medium transition-colors ${
                  active ? "border-brand-500 bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300" : "border-slate-200 text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"
                }`}>
                {s.label}
              </button>
            );
          })}
        </div>
        <div className="mt-3 flex items-center gap-3">
          <button onClick={fetchHistorical} disabled={histLoading || !user} className="btn-primary">
            {histLoading ? <Loader2 size={16} className="animate-spin" /> : <CalendarClock size={16} />}
            {histLoading ? "Fetching..." : "Fetch historical articles"}
          </button>
          {histResult && (
            <span className={`text-xs ${histResult.startsWith("Error") ? "text-rose-600" : "text-emerald-600"}`}>{histResult}</span>
          )}
        </div>
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-300">{error}</div>
      )}

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="card h-72 animate-pulse p-4">
              <div className="h-40 rounded bg-slate-200 dark:bg-slate-800" />
              <div className="mt-3 h-4 w-3/4 rounded bg-slate-200 dark:bg-slate-800" />
              <div className="mt-2 h-3 w-full rounded bg-slate-200 dark:bg-slate-800" />
            </div>
          ))}
        </div>
      ) : articles.length ? (
        <>
          <div className="mb-3 text-sm text-slate-500">{results?.total} articles found, page {results?.page} of {results?.pages}</div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {articles.map((a) => <ArticleCard key={a.id} article={a} />)}
          </div>
          {(results?.pages || 0) > 1 && (
            <div className="mt-6 flex justify-center gap-2">
              <button onClick={() => runSearch(page - 1)} disabled={page <= 1} className="btn-secondary">Previous</button>
              <span className="rounded-lg bg-slate-100 px-3 py-2 text-sm dark:bg-slate-800">{page} / {results?.pages}</span>
              <button onClick={() => runSearch(page + 1)} disabled={page >= (results?.pages || 1)} className="btn-secondary">Next</button>
            </div>
          )}
        </>
      ) : (
        <div className="card flex h-64 flex-col items-center justify-center gap-2 text-center">
          <Filter size={32} className="text-slate-300" />
          <p className="text-sm text-slate-500">No articles match your search.</p>
        </div>
      )}
    </div>
  );
}

function Select({ label, value, onChange, options }: { label: string; value: string; onChange: (v: string) => void; options: { value: string; label: string }[] }) {
  return (
    <div>
      <label className="label">{label}</label>
      <select value={value} onChange={(e) => onChange(e.target.value)} className="input capitalize">
        {options.map((opt) => (
          <option key={opt.value} value={opt.value} className="capitalize">{opt.label}</option>
        ))}
      </select>
    </div>
  );
}