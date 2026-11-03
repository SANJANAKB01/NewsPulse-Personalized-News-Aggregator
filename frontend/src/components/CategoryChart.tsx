import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from "recharts";
import type { CategoriesResponse } from "../types";

interface Props {
  data: CategoriesResponse;
}

const COLORS = ["#2e85ff", "#8b5cf6", "#10b981", "#f59e0b", "#ef4444", "#06b6d4", "#ec4899", "#14b8a6", "#6366f1", "#84cc16"];

export default function CategoryChart({ data }: Props) {
  const byTopic = data.by_topic
    .filter((d) => d.topic)
    .map((d) => ({ name: d.topic!, value: d.count }));

  if (!byTopic.length) {
    return (
      <div className="card flex h-64 items-center justify-center text-sm text-slate-500">
        No category data yet.
      </div>
    );
  }

  return (
    <div className="card p-4">
      <h3 className="mb-3 text-sm font-semibold text-slate-700 dark:text-slate-300">
        Articles by Topic
      </h3>
      <ResponsiveContainer width="100%" height={260}>
        <PieChart>
          <Pie
            data={byTopic}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            outerRadius={90}
            innerRadius={50}
            paddingAngle={2}
          >
            {byTopic.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: "rgba(15,23,42,0.95)",
              border: "1px solid rgba(148,163,184,0.3)",
              borderRadius: 8,
              color: "white",
              fontSize: 12,
            }}
          />
          <Legend
            verticalAlign="bottom"
            iconType="circle"
            wrapperStyle={{ fontSize: 11, paddingTop: 8 }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
