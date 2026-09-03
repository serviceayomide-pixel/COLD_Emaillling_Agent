"use client"

import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid, Area, AreaChart } from "recharts"

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="rounded-xl border border-white/10 bg-slate-900/95 backdrop-blur-xl px-4 py-3 shadow-2xl">
        <p className="text-xs font-semibold text-white mb-2">{label}</p>
        {payload.map((entry: any, i: number) => (
          <div key={i} className="flex items-center gap-2 text-xs">
            <div className="h-2 w-2 rounded-full" style={{ backgroundColor: entry.color }} />
            <span className="text-slate-400 capitalize">{entry.dataKey}:</span>
            <span className="font-semibold text-white">{entry.value}</span>
          </div>
        ))}
      </div>
    )
  }
  return null
}

export function ActivityChart({ data }: { data: any[] }) {
  return (
    <ResponsiveContainer width="100%" height={320}>
      <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
        <defs>
          <linearGradient id="gradientSent" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#818cf8" stopOpacity={0.3} />
            <stop offset="100%" stopColor="#818cf8" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="gradientOpened" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#34d399" stopOpacity={0.3} />
            <stop offset="100%" stopColor="#34d399" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
        <XAxis
          dataKey="date"
          stroke="rgba(255,255,255,0.15)"
          fontSize={11}
          tickLine={false}
          axisLine={false}
          dy={10}
          tick={{ fill: "#64748b" }}
        />
        <YAxis
          stroke="rgba(255,255,255,0.15)"
          fontSize={11}
          tickLine={false}
          axisLine={false}
          dx={-10}
          tick={{ fill: "#64748b" }}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ stroke: "rgba(255,255,255,0.06)" }} />
        <Area
          type="monotone"
          dataKey="sent"
          stroke="#818cf8"
          strokeWidth={2.5}
          fill="url(#gradientSent)"
          dot={false}
          activeDot={{ r: 5, fill: "#818cf8", stroke: "#07090f", strokeWidth: 3 }}
        />
        <Area
          type="monotone"
          dataKey="opened"
          stroke="#34d399"
          strokeWidth={2.5}
          fill="url(#gradientOpened)"
          dot={false}
          activeDot={{ r: 5, fill: "#34d399", stroke: "#07090f", strokeWidth: 3 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}
