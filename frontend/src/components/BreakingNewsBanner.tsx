import { useEffect, useState } from "react";
import { Radio } from "lucide-react";
import { Link } from "react-router-dom";
import type { Article } from "../types";
import { newsApi } from "../api/endpoints";

export default function BreakingNewsBanner() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [current, setCurrent] = useState(0);

  useEffect(() => {
    let mounted = true;
    newsApi.breaking(8).then((data) => {
      if (mounted) setArticles(data.articles);
    }).catch(() => {});
    const interval = setInterval(() => {
      setCurrent((prev) => (prev + 1) % Math.max(1, articles.length));
    }, 5000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, [articles.length]);

  if (!articles.length) return null;
  const article = articles[current];

  return (
    <div className="flex items-center gap-3 overflow-hidden rounded-xl border border-red-200 bg-red-50 px-4 py-2.5 dark:border-red-900/50 dark:bg-red-950/40">
      <span className="flex flex-shrink-0 items-center gap-1.5 rounded-full bg-red-600 px-2 py-0.5 text-xs font-bold uppercase tracking-wider text-white">
        <Radio size={12} /> Breaking
      </span>
      <Link
        to={article.url}
        target="_blank"
        className="line-clamp-1 flex-1 text-sm font-medium text-red-900 hover:underline dark:text-red-200"
      >
        {article.title}
      </Link>
      <span className="hidden text-xs text-red-700 dark:text-red-300 sm:inline">
        {articles.length} stories
      </span>
    </div>
  );
}
