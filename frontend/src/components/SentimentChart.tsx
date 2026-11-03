import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from "recharts";
import type { SentimentResponse } from "../types";

interface Props {
  data: SentimentResponse;
}

export default function SentimentChart({ data }: Props) {
  const chartData = data.distribution.map((d) => ({ name: d.label, value: d.count }));
  const colors: Record<string, string> = {
    positive: "#10b981",
    negative: "#ef4444",
    neutral: "#94a3b8",
  };

  return (
    <div className="card p-4">
      <h3 className="mb-3 text-sm font-semibold text-slate-700 dark:text-slate-300">
        Sentiment Breakdown
      </h3>
      <div className="mb-3 flex items-center gap-2 text-xs text-slate-500">
        <span className="rounded bg-slate-100 px-2 py-0.5 dark:bg-slate-800">
          Avg score: {data.average_score.toFixed(3)}
        </span>
        <span className="rounded bg-slate-100 px-2 py-0.5 dark:bg-slate-800">
          {data.distribution.reduce((s, d) => s + d.count, 0)} articles
        </span>
      </div>
      {chartData.length === 0 ? (
        <div className="flex h-48 items-center justify-center text-sm text-slate-500">
          No sentiment data yet.
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 16 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.2)" />
            <XAxis type="number" tick={{ fontSize: 11, fill: "currentColor" }} allowDecimals={false} />
            <YAxis type="category" dataKey="name" tick={{ fontSize: 11, fill: "currentColor" }} width={80} />
            <Tooltip
              cursor={{ fill: "rgba(148,163,184,0.1)" }}
              contentStyle={{
                backgroundColor: "rgba(15,23,42,0.95)",
                border: "1px solid rgba(148,163,184,0.3)",
                borderRadius: 8,
                color: "white",
                fontSize: 12,
              }}
            />
            <Bar dataKey="value" radius={[0, 6, 6, 0]}>
              {chartData.map((entry, i) => (
                <Cell key={i} fill={colors[entry.name] || "#94a3b8"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
