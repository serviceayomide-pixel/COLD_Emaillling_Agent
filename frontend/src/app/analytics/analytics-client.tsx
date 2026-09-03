"use client"

import { useState, useEffect } from "react"
import { BarChart3, TrendingUp, Users, MailCheck, Send, ThumbsUp, CalendarCheck, ArrowUpRight, ArrowDownRight } from "lucide-react"
import { useRouter } from "next/navigation"
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts"
import { supabase } from "@/lib/supabase"

type Props = {
  totalLeads: number
  emailedLeads: number
  repliedLeads: number
  replyRate: string
  positiveRate: string
  chartData: { week: string; sent: number; opened: number; replied: number }[]
  enrichedPercent: number
  notEnrichedPercent: number
  topSubjects: { subject: string; count: number }[]
}

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

export default function AnalyticsClient(props: Props) {
  const router = useRouter()

  useEffect(() => {
    const leadsSub = supabase
      .channel("analytics:leads")
      .on("postgres_changes", { event: "*", schema: "public", table: "cqc_leads" }, () => router.refresh())
      .subscribe()

    const logsSub = supabase
      .channel("analytics:logs")
      .on("postgres_changes", { event: "*", schema: "public", table: "campaign_logs" }, () => router.refresh())
      .subscribe()

    return () => {
      supabase.removeChannel(leadsSub)
      supabase.removeChannel(logsSub)
    }
  }, [router])

  const performanceMetrics = [
    { label: "Total Leads", value: props.totalLeads.toLocaleString(), change: null, icon: Users, color: "text-cyan-400" },
    { label: "Emails Sent", value: props.emailedLeads.toLocaleString(), change: null, icon: Send, color: "text-indigo-400" },
    { label: "Total Replies", value: props.replyRate, change: null, icon: MailCheck, color: "text-emerald-400" },
    { label: "Positive Replies", value: props.positiveRate, change: null, icon: ThumbsUp, color: "text-amber-400" },
  ]

  const channelData = [
    { name: "Enriched", value: props.enrichedPercent, color: "#818cf8" },
    { name: "Not Enriched", value: props.notEnrichedPercent, color: "#22d3ee" },
  ]

  return (
    <>
      <header className="border-b border-white/[0.06] bg-[#07090f]/80 backdrop-blur-2xl">
        <div className="flex items-center justify-between px-4 py-4 md:px-8 md:py-5">
          <div>
            <h2 className="text-xl font-semibold text-white tracking-tight">Analytics</h2>
            <p className="text-xs text-slate-500 mt-0.5">Campaign performance and enrichment insights</p>
          </div>
        </div>
      </header>

      <main className="px-4 py-6 md:px-8 md:py-8 space-y-6">
        {/* Performance Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {performanceMetrics.map((metric) => (
            <div key={metric.label} className="rounded-2xl border border-white/[0.06] bg-white/[0.03] backdrop-blur-xl p-4 md:p-5">
              <div className="flex items-center justify-between mb-3">
                <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">{metric.label}</span>
                <metric.icon className={`h-4 w-4 ${metric.color}`} />
              </div>
              <div className="flex items-center gap-2">
                <p className="text-2xl font-bold text-white">{metric.value}</p>
                {metric.change !== null && (
                  <span className={`flex items-center text-xs font-medium ${(metric.change as number) >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                    {(metric.change as number) >= 0 ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
                    {Math.abs(metric.change as number)}%
                  </span>
                )}
              </div>
              <p className="text-[10px] text-slate-600 mt-1">
                {props.emailedLeads === 0 ? "Awaiting first campaign" : "Live data from Supabase"}
              </p>
            </div>
          ))}
        </div>

        {/* Charts Row */}
        <div className="grid gap-6 grid-cols-1 lg:grid-cols-12">
          {/* Outreach Over Time */}
          <div className="col-span-1 lg:col-span-8 rounded-2xl border border-white/[0.06] bg-white/[0.03] backdrop-blur-xl overflow-x-auto">
            <div className="p-4 md:p-6 pb-2 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="flex items-center justify-center h-8 w-8 rounded-lg bg-indigo-500/10">
                  <TrendingUp className="h-4 w-4 text-indigo-400" />
                </div>
                <h3 className="text-base font-semibold text-white">Outreach Performance</h3>
              </div>
              <div className="flex flex-wrap items-center gap-4 text-xs">
                <div className="flex items-center gap-1.5"><div className="h-2 w-2 rounded-full bg-indigo-400" /><span className="text-slate-400">Sent</span></div>
                <div className="flex items-center gap-1.5"><div className="h-2 w-2 rounded-full bg-cyan-400" /><span className="text-slate-400">Opened</span></div>
                <div className="flex items-center gap-1.5"><div className="h-2 w-2 rounded-full bg-emerald-400" /><span className="text-slate-400">Replied</span></div>
              </div>
            </div>
            <div className="px-4 pb-6">
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={props.chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="gSent" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#818cf8" stopOpacity={0.3} /><stop offset="100%" stopColor="#818cf8" stopOpacity={0} /></linearGradient>
                    <linearGradient id="gOpened" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#22d3ee" stopOpacity={0.3} /><stop offset="100%" stopColor="#22d3ee" stopOpacity={0} /></linearGradient>
                    <linearGradient id="gReplied" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#34d399" stopOpacity={0.3} /><stop offset="100%" stopColor="#34d399" stopOpacity={0} /></linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
                  <XAxis dataKey="week" stroke="rgba(255,255,255,0.15)" fontSize={11} tickLine={false} axisLine={false} tick={{ fill: "#64748b" }} />
                  <YAxis stroke="rgba(255,255,255,0.15)" fontSize={11} tickLine={false} axisLine={false} tick={{ fill: "#64748b" }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Area type="monotone" dataKey="sent" stroke="#818cf8" strokeWidth={2} fill="url(#gSent)" dot={false} />
                  <Area type="monotone" dataKey="opened" stroke="#22d3ee" strokeWidth={2} fill="url(#gOpened)" dot={false} />
                  <Area type="monotone" dataKey="replied" stroke="#34d399" strokeWidth={2} fill="url(#gReplied)" dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Enrichment Source Breakdown */}
          <div className="col-span-1 lg:col-span-4 rounded-2xl border border-white/[0.06] bg-white/[0.03] backdrop-blur-xl">
            <div className="p-4 md:p-6 pb-2">
              <div className="flex items-center gap-3">
                <div className="flex items-center justify-center h-8 w-8 rounded-lg bg-violet-500/10">
                  <BarChart3 className="h-4 w-4 text-violet-400" />
                </div>
                <h3 className="text-base font-semibold text-white">Enrichment Status</h3>
              </div>
            </div>
            <div className="flex flex-col items-center pb-6">
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie data={channelData} cx="50%" cy="50%" innerRadius={55} outerRadius={75} paddingAngle={4} dataKey="value" stroke="none">
                    {channelData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex items-center gap-5">
                {channelData.map((ch) => (
                  <div key={ch.name} className="flex items-center gap-2">
                    <div className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: ch.color }} />
                    <span className="text-xs text-slate-400">{ch.name} ({ch.value}%)</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Best Performing Section */}
        <div className="rounded-2xl border border-white/[0.06] bg-white/[0.03] backdrop-blur-xl p-6">
          <div className="flex items-center gap-3 mb-5">
            <div className="flex items-center justify-center h-8 w-8 rounded-lg bg-emerald-500/10">
              <TrendingUp className="h-4 w-4 text-emerald-400" />
            </div>
            <h3 className="text-base font-semibold text-white">Top Subject Lines</h3>
          </div>
          <div className="space-y-3">
            {props.topSubjects.length > 0 ? (
              props.topSubjects.map((line, i) => (
                <div key={i} className="flex items-center justify-between p-4 rounded-xl bg-white/[0.02] border border-white/[0.04]">
                  <div className="flex items-center gap-3">
                    <span className="flex items-center justify-center h-7 w-7 rounded-lg bg-white/[0.04] text-xs font-bold text-slate-400">
                      {i + 1}
                    </span>
                    <span className="text-sm text-slate-300">{line.subject}</span>
                  </div>
                  <div className="flex items-center gap-6">
                    <div className="text-right">
                      <p className="text-xs text-slate-500">Used</p>
                      <p className="text-sm font-semibold text-cyan-400">{line.count}×</p>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              [
                { subject: "No subject lines generated yet", count: "—" },
              ].map((line, i) => (
                <div key={i} className="flex items-center justify-between p-4 rounded-xl bg-white/[0.02] border border-white/[0.04]">
                  <div className="flex items-center gap-3">
                    <span className="flex items-center justify-center h-7 w-7 rounded-lg bg-white/[0.04] text-xs font-bold text-slate-400">
                      {i + 1}
                    </span>
                    <span className="text-sm text-slate-500 italic">{line.subject}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </main>
    </>
  )
}
