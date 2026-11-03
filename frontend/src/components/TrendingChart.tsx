import { useMemo } from "react";
import { BarChart, Bar, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import type { TrendingItem } from "../types";

interface Props {
  data: TrendingItem[];
}

const COLORS = ["#2e85ff", "#8b5cf6", "#10b981", "#f59e0b", "#ef4444", "#06b6d4", "#ec4899"];

export default function TrendingChart({ data }: Props) {
  const chartData = useMemo(
    () => data.slice(0, 8).map((d) => ({ ...d, topic: d.topic })),
    [data],
  );

  if (!chartData.length) {
    return (
      <div className="card flex h-64 items-center justify-center text-sm text-slate-500">
        No trending topics in the last 24 hours.
      </div>
    );
  }

  return (
    <div className="card p-4">
      <h3 className="mb-3 text-sm font-semibold text-slate-700 dark:text-slate-300">
        Trending Topics <span className="text-xs font-normal text-slate-400">(last 24h)</span>
      </h3>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={chartData} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.2)" />
          <XAxis
            dataKey="topic"
            tick={{ fontSize: 11, fill: "currentColor" }}
            interval={0}
            angle={-15}
            textAnchor="end"
            height={50}
          />
          <YAxis tick={{ fontSize: 11, fill: "currentColor" }} allowDecimals={false} />
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
          <Bar dataKey="count" radius={[6, 6, 0, 0]}>
            {chartData.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
