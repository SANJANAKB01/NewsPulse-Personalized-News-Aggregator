import { useEffect, useState } from "react";
import { CheckCircle2, Mail } from "lucide-react";
import { newsletterApi, newsApi } from "../api/endpoints";
import type { TopicsResponse, NewsletterSubscriber } from "../types";

const FREQUENCIES = [
  { value: "daily", label: "Daily" },
  { value: "weekly", label: "Weekly" },
  { value: "off", label: "Pause" },
];

export default function Newsletter() {
  const [email, setEmail] = useState("");
  const [frequency, setFrequency] = useState("daily");
  const [topics, setTopics] = useState<string[]>([]);
  const [availableTopics, setAvailableTopics] = useState<TopicsResponse | null>(null);
  const [subscribers, setSubscribers] = useState<NewsletterSubscriber[]>([]);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    newsApi.topics().then(setAvailableTopics).catch(() => {});
    newsletterApi.list().then((data) => setSubscribers(data.subscribers)).catch(() => {});
  }, []);

  const toggleTopic = (topic: string) => {
    setTopics((prev) =>
      prev.includes(topic) ? prev.filter((t) => t !== topic) : [...prev, topic],
    );
  };

  const subscribe = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    try {
      const result = await newsletterApi.subscribe(email, frequency, topics);
      setSuccess(`Subscribed ${email}. Confirmation token: ${result.confirm_token}`);
      setEmail("");
      const data = await newsletterApi.list();
      setSubscribers(data.subscribers);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const unsubscribe = async (subscriber: NewsletterSubscriber) => {
    try {
      await newsletterApi.unsubscribe(subscriber.email);
      const data = await newsletterApi.list();
      setSubscribers(data.subscribers);
    } catch (err) {
      alert((err as Error).message);
    }
  };

  return (
    <div className="mx-auto max-w-4xl px-4 py-6 sm:px-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold tracking-tight">Newsletter</h1>
        <p className="mt-1 text-sm text-slate-500">
          Get a personalized news digest in your inbox
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="card p-6">
          <div className="mb-4 flex items-center gap-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-600 text-white">
              <Mail size={18} />
            </div>
            <div>
              <h2 className="font-semibold">Subscribe</h2>
              <p className="text-xs text-slate-500">Choose your topics and frequency</p>
            </div>
          </div>

          {error && (
            <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-300">
              {error}
            </div>
          )}
          {success && (
            <div className="mb-4 flex items-start gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700 dark:border-emerald-900/50 dark:bg-emerald-950/40 dark:text-emerald-300">
              <CheckCircle2 size={16} className="mt-0.5 flex-shrink-0" />
              <span>{success}</span>
            </div>
          )}

          <form onSubmit={subscribe} className="space-y-4">
            <div>
              <label className="label">Email address</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="input"
                placeholder="you@example.com"
              />
            </div>
            <div>
              <label className="label">Frequency</label>
              <div className="flex gap-2">
                {FREQUENCIES.map((f) => (
                  <button
                    key={f.value}
                    type="button"
                    onClick={() => setFrequency(f.value)}
                    className={`flex-1 rounded-lg border px-3 py-2 text-sm font-medium ${
                      frequency === f.value
                        ? "border-brand-500 bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300"
                        : "border-slate-200 text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"
                    }`}
                  >
                    {f.label}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="label">Topics to include</label>
              <div className="flex flex-wrap gap-1.5">
                {(availableTopics?.topics || []).map((t) => {
                  const active = topics.includes(t);
                  return (
                    <button
                      key={t}
                      type="button"
                      onClick={() => toggleTopic(t)}
                      className={`rounded-lg px-2.5 py-1 text-xs font-medium capitalize ${
                        active
                          ? "bg-brand-600 text-white"
                          : "bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300"
                      }`}
                    >
                      {t}
                    </button>
                  );
                })}
              </div>
              <p className="mt-1 text-xs text-slate-500">
                Leave empty to include all topics
              </p>
            </div>
            <button type="submit" className="btn-primary w-full">Subscribe</button>
          </form>
        </div>

        <div className="card p-6">
          <h2 className="mb-4 font-semibold">Current subscribers</h2>
          {subscribers.length ? (
            <ul className="divide-y divide-slate-100 dark:divide-slate-800">
              {subscribers.map((s) => (
                <li key={s.id} className="flex items-start justify-between gap-3 py-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">{s.email}</span>
                      {s.confirmed ? (
                        <span className="badge-positive">Confirmed</span>
                      ) : (
                        <span className="badge-neutral">Pending</span>
                      )}
                    </div>
                    <div className="mt-0.5 text-xs text-slate-500">
                      {s.frequency} · {s.topics.length ? s.topics.join(", ") : "all topics"}
                    </div>
                  </div>
                  <button
                    onClick={() => unsubscribe(s)}
                    className="text-xs text-rose-600 hover:underline"
                  >
                    Unsubscribe
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <div className="flex h-32 items-center justify-center text-sm text-slate-500">
              No subscribers yet
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
