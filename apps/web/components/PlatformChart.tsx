"use client";

import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

interface Props {
  data: Record<string, number>;
}

const COLORS: Record<string, string> = {
  Danawa: "#7a0024",
  Reddit: "#ff4500",
  "Naver Blog": "#03c75a",
  YouTube: "#ff0000",
  "X/Twitter": "#000000",
};

export function PlatformChart({ data }: Props) {
  const chartData = Object.entries(data).map(([name, value]) => ({ name, value }));

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={chartData} barSize={28}>
        <CartesianGrid strokeDasharray="3 3" stroke="#ebeef3" vertical={false} />
        <XAxis dataKey="name" tick={{ fontSize: 12, fill: "#5a5e6a" }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fontSize: 11, fill: "#5a5e6a" }} axisLine={false} tickLine={false} width={24} />
        <Tooltip
          contentStyle={{ border: "1px solid #ebeef3", borderRadius: 8, fontSize: 13 }}
          cursor={{ fill: "#f1f4f9" }}
        />
        <Bar dataKey="value" radius={[4, 4, 0, 0]}>
          {chartData.map((entry) => (
            <Cell key={entry.name} fill={COLORS[entry.name] ?? "#7a0024"} fillOpacity={0.85} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
