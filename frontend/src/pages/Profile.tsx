import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Check, Clock, History } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import { bookmarksApi, newsApi } from "../api/endpoints";
import type { Article } from "../types";

const ALL_TOPICS = [
  "technology", "sports", "finance", "business", "travel",
  "entertainment", "health", "science", "politics", "world",
];

export default function Profile() {
  const { user, updatePreferences, logout } = useAuth();
  const [selected, setSelected] = useState<string[]>(user?.preferences || []);
  const [saved, setSaved] = useState(false);
  const [history, setHistory] = useState<{ article: Article; read_at: string }[]>([]);
  const [stats, setStats] = useState<{ bookmarks: number; reads: number } | null>(null);

  useEffect(() => {
    setSelected(user?.preferences || []);
  }, [user]);

  useEffect(() => {
    bookmarksApi.history().then((data) => setHistory(data.history)).catch(() => {});
    bookmarksApi.list().then((data) => {
      setStats({ bookmarks: data.count, reads: 0 });
    }).catch(() => {});
  }, []);

  const toggle = (topic: string) => {
    setSelected((prev) =>
      prev.includes(topic) ? prev.filter((t) => t !== topic) : [...prev, topic],
    );
    setSaved(false);
  };

  const save = async () => {
    try {
      await updatePreferences(selected);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (err) {
      alert((err as Error).message);
    }
  };

  if (!user) return null;

  return (
    <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6">
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Profile</h1>
          <p className="mt-1 text-sm text-slate-500">
            Signed in as <span className="font-medium">{user.email}</span>
          </p>
        </div>
        <button onClick={logout} className="btn-secondary">Sign out</button>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="card p-4">
          <div className="text-2xl font-bold">{stats?.bookmarks ?? 0}</div>
          <div className="text-xs text-slate-500">Saved articles</div>
        </div>
        <div className="card p-4">
          <div className="text-2xl font-bold">{history.length}</div>
          <div className="text-xs text-slate-500">Articles read</div>
        </div>
        <div className="card p-4">
          <div className="text-2xl font-bold">{user.preferences.length}</div>
          <div className="text-xs text-slate-500">Topics selected</div>
        </div>
      </div>

      <div className="mt-6 card p-5">
        <h2 className="mb-1 text-lg font-semibold">Your preferred topics</h2>
        <p className="mb-4 text-sm text-slate-500">
          We use these to personalize your feed and recommendations.
        </p>
        <div className="flex flex-wrap gap-2">
          {ALL_TOPICS.map((topic) => {
            const active = selected.includes(topic);
            return (
              <button
                key={topic}
                onClick={() => toggle(topic)}
                className={`flex items-center gap-1 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                  active
                    ? "bg-brand-600 text-white"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                }`}
              >
                {active && <Check size={14} />}
                <span className="capitalize">{topic}</span>
              </button>
            );
          })}
        </div>
        <div className="mt-4 flex items-center gap-3">
          <button onClick={save} className="btn-primary">Save preferences</button>
          {saved && (
            <span className="flex items-center gap-1 text-sm text-emerald-600">
              <Check size={14} /> Saved
            </span>
          )}
        </div>
      </div>

      <div className="mt-6 card p-5">
        <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold">
          <History size={18} /> Recent reading history
        </h2>
        {history.length ? (
          <ul className="divide-y divide-slate-100 dark:divide-slate-800">
            {history.slice(0, 10).map((item, i) => (
              <li key={i} className="flex items-start justify-between gap-4 py-3">
                <div className="min-w-0 flex-1">
                  <a href={item.article?.url} target="_blank" rel="noopener noreferrer"
                     className="line-clamp-1 text-sm font-medium hover:text-brand-600">
                    {item.article?.title}
                  </a>
                  <div className="text-xs text-slate-500">{item.article?.source_name}</div>
                </div>
                <div className="flex flex-shrink-0 items-center gap-1 text-xs text-slate-400">
                  <Clock size={12} />
                  {new Date(item.read_at).toLocaleDateString()}
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <div className="text-sm text-slate-500">
            No history yet. <Link to="/feed" className="text-brand-600 hover:underline">Read some articles</Link> to start tracking.
          </div>
        )}
      </div>
    </div>
  );
}
