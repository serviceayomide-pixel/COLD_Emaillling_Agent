"use client"

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts"

interface StatusBreakdownProps {
  totalLeads: number
  verifiedEmails: number
}

export function StatusBreakdown({ totalLeads, verifiedEmails }: StatusBreakdownProps) {
  const pending = totalLeads - verifiedEmails
  const data = [
    { name: "Verified", value: verifiedEmails, color: "#22d3ee" },
    { name: "Pending", value: pending > 0 ? pending : 0, color: "#1e293b" },
  ]

  const percentage = totalLeads > 0 ? ((verifiedEmails / totalLeads) * 100).toFixed(1) : "0.0"

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="rounded-xl border border-white/10 bg-slate-900/95 backdrop-blur-xl px-4 py-3 shadow-2xl">
          <p className="text-xs font-semibold text-white">
            {payload[0].name}: {payload[0].value.toLocaleString()}
          </p>
        </div>
      )
    }
    return null
  }

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-[180px] h-[180px]">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={80}
              paddingAngle={3}
              dataKey="value"
              stroke="none"
              startAngle={90}
              endAngle={-270}
            >
              {data.map((entry, index) => (
                <Cell key={index} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>
        {/* Center Label */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold text-white">{percentage}%</span>
          <span className="text-[10px] text-slate-500 font-medium">Enriched</span>
        </div>
      </div>
      {/* Legend */}
      <div className="flex items-center gap-5 mt-4">
        <div className="flex items-center gap-2">
          <div className="h-2.5 w-2.5 rounded-full bg-cyan-400" />
          <span className="text-xs text-slate-400">Verified ({verifiedEmails.toLocaleString()})</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-2.5 w-2.5 rounded-full bg-slate-700" />
          <span className="text-xs text-slate-400">Pending ({(totalLeads - verifiedEmails).toLocaleString()})</span>
        </div>
      </div>
    </div>
  )
}
