import { Bookmark, Clock, ExternalLink, Share2 } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import type { Article } from "../types";
import { bookmarksApi, newsApi } from "../api/endpoints";
import { useAuth } from "../contexts/AuthContext";

interface Props {
  article: Article;
  bookmarked?: boolean;
  onBookmarkToggle?: (articleId: number, isBookmarked: boolean) => void;
  variant?: "default" | "compact";
}

const topicColors: Record<string, string> = {
  technology: "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300",
  sports: "bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300",
  business: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300",
  finance: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300",
  health: "bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300",
  science: "bg-violet-100 text-violet-700 dark:bg-violet-900/40 dark:text-violet-300",
  entertainment: "bg-pink-100 text-pink-700 dark:bg-pink-900/40 dark:text-pink-300",
  travel: "bg-cyan-100 text-cyan-700 dark:bg-cyan-900/40 dark:text-cyan-300",
  politics: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300",
  world: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
};

function sentimentBadge(label?: string) {
  if (label === "positive") return <span className="badge-positive">Positive</span>;
  if (label === "negative") return <span className="badge-negative">Negative</span>;
  return <span className="badge-neutral">Neutral</span>;
}

function formatPublished(iso?: string | null) {
  if (!iso) return "";
  const date = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const minutes = Math.floor(diffMs / 60000);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return date.toLocaleDateString();
}

export default function ArticleCard({ article, bookmarked = false, onBookmarkToggle, variant = "default" }: Props) {
  const { user } = useAuth();
  const [isBookmarked, setIsBookmarked] = useState(bookmarked);
  const [shareOpen, setShareOpen] = useState(false);
  const [shareCount, setShareCount] = useState(article.share_count || 0);

  const handleBookmark = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!user) {
      window.location.href = "/login";
      return;
    }
    try {
      if (isBookmarked) {
        await bookmarksApi.remove(article.id);
        setIsBookmarked(false);
        onBookmarkToggle?.(article.id, false);
      } else {
        await bookmarksApi.add(article.id);
        setIsBookmarked(true);
        onBookmarkToggle?.(article.id, true);
      }
    } catch (err) {
      alert((err as Error).message);
    }
  };

  const handleShare = async (platform: string) => {
    setShareOpen(false);
    try {
      const result = await newsApi.share(article.id, platform);
      setShareCount(result.share_count);
      const shareUrl = article.url;
      if (platform === "twitter") {
        window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(article.title)}&url=${encodeURIComponent(shareUrl)}`, "_blank");
      } else if (platform === "facebook") {
        window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}`, "_blank");
      } else if (platform === "linkedin") {
        window.open(`https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(shareUrl)}`, "_blank");
      } else if (platform === "email") {
        window.location.href = `mailto:?subject=${encodeURIComponent(article.title)}&body=${encodeURIComponent(shareUrl)}`;
      } else if (platform === "copy") {
        navigator.clipboard?.writeText(shareUrl);
      }
    } catch (err) {
      alert((err as Error).message);
    }
  };

  const handleRead = async () => {
    if (user) {
      try {
        await newsApi.markRead(article.id);
      } catch { /* ignore */ }
    }
  };

  const topicClass = topicColors[article.topic || "world"] || topicColors.world;

  if (variant === "compact") {
    return (
      <Link to={article.url} target="_blank" onClick={handleRead} className="card flex gap-3 p-3 transition-shadow hover:shadow-md">
        {article.url_to_image && (
          <img
            src={article.url_to_image}
            alt=""
            className="h-16 w-16 flex-shrink-0 rounded-lg object-cover"
            onError={(e) => ((e.target as HTMLImageElement).style.display = "none")}
          />
        )}
        <div className="min-w-0 flex-1">
          <h3 className="line-clamp-2 text-sm font-semibold">{article.title}</h3>
          <div className="mt-1 flex items-center gap-2 text-xs text-slate-500">
            <span className={`chip ${topicClass}`}>{article.topic}</span>
            <span>{formatPublished(article.published_at)}</span>
          </div>
        </div>
      </Link>
    );
  }

  return (
    <article className="card overflow-hidden transition-shadow hover:shadow-md">
      {article.url_to_image && (
        <a href={article.url} target="_blank" rel="noopener noreferrer" onClick={handleRead}>
          <img
            src={article.url_to_image}
            alt={article.title}
            className="h-48 w-full object-cover"
            onError={(e) => ((e.target as HTMLImageElement).parentElement!.style.display = "none")}
          />
        </a>
      )}
      <div className="flex flex-col gap-3 p-4">
        <div className="flex flex-wrap items-center gap-2">
          <span className={`chip ${topicClass}`}>{article.topic || "world"}</span>
          {article.is_breaking && <span className="badge-breaking">Breaking</span>}
          {sentimentBadge(article.sentiment_label)}
          <span className="ml-auto text-xs text-slate-500">{formatPublished(article.published_at)}</span>
        </div>

        <a href={article.url} target="_blank" rel="noopener noreferrer" onClick={handleRead}>
          <h3 className="line-clamp-2 text-lg font-semibold leading-snug hover:text-brand-600">
            {article.title}
          </h3>
        </a>

        {article.description && (
          <p className="line-clamp-3 text-sm text-slate-600 dark:text-slate-400">
            {article.description}
          </p>
        )}

        <div className="flex items-center justify-between text-xs text-slate-500">
          <div className="flex items-center gap-3">
            {article.source_name && <span className="font-medium text-slate-700 dark:text-slate-300">{article.source_name}</span>}
            {article.reading_time_min ? (
              <span className="flex items-center gap-1">
                <Clock size={12} /> {article.reading_time_min} min
              </span>
            ) : null}
            {shareCount > 0 && <span>{shareCount} shares</span>}
          </div>
        </div>

        <div className="flex items-center justify-between border-t border-slate-100 pt-3 dark:border-slate-800">
          <button
            onClick={handleBookmark}
            className={`btn-ghost text-xs ${isBookmarked ? "text-brand-600" : ""}`}
            title={isBookmarked ? "Remove bookmark" : "Save article"}
          >
            <Bookmark size={16} fill={isBookmarked ? "currentColor" : "none"} />
            {isBookmarked ? "Saved" : "Save"}
          </button>

          <div className="relative">
            <button
              onClick={(e) => { e.preventDefault(); e.stopPropagation(); setShareOpen(!shareOpen); }}
              className="btn-ghost text-xs"
              title="Share"
            >
              <Share2 size={16} /> Share
            </button>
            {shareOpen && (
              <div className="absolute bottom-full right-0 mb-2 w-36 rounded-lg border border-slate-200 bg-white py-1 shadow-lg dark:border-slate-700 dark:bg-slate-800">
                {[
                  { label: "Twitter", value: "twitter" },
                  { label: "Facebook", value: "facebook" },
                  { label: "LinkedIn", value: "linkedin" },
                  { label: "Email", value: "email" },
                  { label: "Copy link", value: "copy" },
                ].map((opt) => (
                  <button
                    key={opt.value}
                    onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleShare(opt.value); }}
                    className="block w-full px-3 py-1.5 text-left text-xs hover:bg-slate-100 dark:hover:bg-slate-700"
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            )}
          </div>

          <a href={article.url} target="_blank" rel="noopener noreferrer" onClick={handleRead} className="btn-ghost text-xs">
            Read <ExternalLink size={14} />
          </a>
        </div>
      </div>
    </article>
  );
}
