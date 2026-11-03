interface TopicItem {
  topic: string;
  count: number;
}

interface Props {
  items: TopicItem[];
  active?: string;
  onToggle?: (topic: string) => void;
  title?: string;
}

export default function CategoryFilter({ items, active, onToggle, title = "Topics" }: Props) {
  if (!items.length) return null;
  const max = Math.max(...items.map((i) => i.count), 1);

  return (
    <div className="card p-4">
      <h3 className="mb-3 text-sm font-semibold text-slate-700 dark:text-slate-300">{title}</h3>
      <div className="flex flex-wrap gap-2">
        {items.map((item) => {
          const isActive = active === item.topic;
          const intensity = Math.min(100, Math.round((item.count / max) * 100));
          return (
            <button
              key={item.topic}
              onClick={() => onToggle?.(item.topic)}
              className={`group relative flex items-center gap-2 overflow-hidden rounded-lg border px-2.5 py-1.5 text-xs font-medium transition-all ${
                isActive
                  ? "border-brand-500 bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300"
                  : "border-slate-200 text-slate-600 hover:border-slate-300 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
              }`}
              title={`${item.count} articles`}
            >
              <span className="capitalize">{item.topic}</span>
              <span className="rounded-full bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-600 dark:bg-slate-700 dark:text-slate-300">
                {item.count}
              </span>
              <span
                className="absolute inset-x-0 bottom-0 h-0.5 bg-brand-400/40 dark:bg-brand-500/40"
                style={{ width: `${intensity}%` }}
              />
            </button>
          );
        })}
      </div>
    </div>
  );
}
