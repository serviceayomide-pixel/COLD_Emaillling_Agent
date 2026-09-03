"use client"

import { useEffect, useState, useRef } from "react"
import { Users, MailCheck, Send, BarChart3, Reply, ThumbsUp, CalendarCheck, Activity, Zap, TrendingUp, Clock, ChevronRight, Bell } from "lucide-react"
import { ActivityChart } from "@/components/activity-chart"
import { LeadManager } from "@/components/lead-manager"
import { EnrichmentFunnel } from "@/components/enrichment-funnel"
import { LiveActivityFeed } from "@/components/live-activity-feed"
import { StatusBreakdown } from "@/components/status-breakdown"
import { DashboardLayout } from "@/components/dashboard-layout"
import { supabase } from "@/lib/supabase"

interface DashboardClientProps {
  initialTotalLeads: number
  initialVerifiedEmails: number
  initialRecentLeads: any[]
  initialEmailsSent: number
  initialOpenRate: number
  initialReplyRate: number
  initialInterestRate: number
  initialMeetingsBooked: number
  initialInterestedCount: number
  initialChartData: any[]
  activeMonthNumber?: number
}

/* Animated counter that smoothly ticks up */
function AnimatedNumber({ value, duration = 800 }: { value: number; duration?: number }) {
  const [display, setDisplay] = useState(value)
  const prevValue = useRef(value)

  useEffect(() => {
    if (prevValue.current === value) return
    const start = prevValue.current
    const diff = value - start
    const startTime = performance.now()

    const animate = (now: number) => {
      const elapsed = now - startTime
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setDisplay(Math.round(start + diff * eased))
      if (progress < 1) requestAnimationFrame(animate)
    }

    requestAnimationFrame(animate)
    prevValue.current = value
  }, [value, duration])

  return <>{display.toLocaleString()}</>
}

/* Glowing pulse dot */
function PulseIndicator({ color = "emerald" }: { color?: string }) {
  const colorMap: Record<string, string> = {
    emerald: "bg-emerald-400",
    indigo: "bg-indigo-400",
    amber: "bg-amber-400",
  }
  return (
    <span className="relative flex h-2 w-2">
      <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${colorMap[color]} opacity-75`} />
      <span className={`relative inline-flex rounded-full h-2 w-2 ${colorMap[color]}`} />
    </span>
  )
}

/* Glassmorphism stat card */
function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  gradient,
  animate = false,
}: {
  title: string
  value: number | string
  subtitle: string
  icon: any
  gradient: string
  animate?: boolean
}) {
  return (
    <div className="group relative overflow-hidden rounded-2xl border border-white/[0.06] bg-white/[0.03] backdrop-blur-xl p-5 transition-all duration-300 hover:border-white/[0.12] hover:bg-white/[0.05] hover:shadow-2xl hover:shadow-indigo-500/5 hover:-translate-y-0.5">
      <div className={`absolute -top-12 -right-12 h-32 w-32 rounded-full ${gradient} opacity-10 blur-2xl transition-opacity duration-500 group-hover:opacity-20`} />
      <div className="relative z-10">
        <div className="flex items-center justify-between mb-4">
          <span className="text-[13px] font-medium tracking-wide text-slate-400 uppercase">{title}</span>
          <div className={`flex items-center justify-center h-9 w-9 rounded-xl ${gradient} shadow-lg`}>
            <Icon className="h-4 w-4 text-white" />
          </div>
        </div>
        <div className="text-3xl font-bold text-white tracking-tight mb-1">
          {animate && typeof value === "number" ? <AnimatedNumber value={value} /> : value}
        </div>
        <p className="text-xs text-slate-500 font-medium">{subtitle}</p>
      </div>
    </div>
  )
}

/* Glass panel wrapper */
function GlassPanel({
  children,
  className = "",
}: {
  children: React.ReactNode
  className?: string
}) {
  return (
    <div className={`relative overflow-hidden rounded-2xl border border-white/[0.06] bg-white/[0.03] backdrop-blur-xl ${className}`}>
      {children}
    </div>
  )
}

/* Panel header */
function PanelHeader({
  icon: Icon,
  iconBg,
  iconColor,
  title,
  subtitle,
  action,
}: {
  icon: any
  iconBg: string
  iconColor: string
  title: string
  subtitle?: string
  action?: React.ReactNode
}) {
  return (
    <div className="flex items-center justify-between p-6 pb-4">
      <div className="flex items-center gap-3">
        <div className={`flex items-center justify-center h-8 w-8 rounded-lg ${iconBg}`}>
          <Icon className={`h-4 w-4 ${iconColor}`} />
        </div>
        <div>
          <h3 className="text-base font-semibold text-white">{title}</h3>
          {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
        </div>
      </div>
      {action}
    </div>
  )
}

export function DashboardClient({
  initialTotalLeads,
  initialVerifiedEmails,
  initialRecentLeads,
  initialEmailsSent,
  initialOpenRate,
  initialReplyRate,
  initialInterestRate,
  initialMeetingsBooked,
  initialInterestedCount,
  initialChartData,
  activeMonthNumber,
}: DashboardClientProps) {
  const [totalLeads, setTotalLeads] = useState(initialTotalLeads)
  const [verifiedEmails, setVerifiedEmails] = useState(initialVerifiedEmails)
  const [recentLeads, setRecentLeads] = useState(initialRecentLeads)
  const [emailsSent, setEmailsSent] = useState(initialEmailsSent)
  const [openRate, setOpenRate] = useState(initialOpenRate)
  const [replyRate, setReplyRate] = useState(initialReplyRate)
  const [interestRate, setInterestRate] = useState(initialInterestRate)
  const [meetingsBooked, setMeetingsBooked] = useState(initialMeetingsBooked)
  const [interestedCount, setInterestedCount] = useState(initialInterestedCount)
  const [chartData, setChartData] = useState(initialChartData)
  const [lastUpdated, setLastUpdated] = useState(new Date())
  const [searchQuery, setSearchQuery] = useState("")

  useEffect(() => {
    const refreshStats = async () => {
      const { data: metrics } = await supabase.rpc('get_global_dashboard_metrics')
      
      if (metrics) {
        setTotalLeads(metrics.total_leads || 0)
        setVerifiedEmails(metrics.verified_leads || 0)
        setEmailsSent(metrics.total_emails_sent || 0)
        setOpenRate(metrics.total_emails_opened || 0)
        setReplyRate(metrics.total_replied_count || 0)
        setInterestRate(metrics.total_interested_count || 0)
        setMeetingsBooked(metrics.meetings_booked || 0)
        setInterestedCount(metrics.total_interested_count || 0)
        setChartData(metrics.chart_data || [])
      }

      const { data: newLeads } = await supabase
        .from("cqc_leads")
        .select("*")
        .eq("enrichment_status", "enriched")
        .order("enriched_at", { ascending: false })
        .limit(50)

      if (newLeads) setRecentLeads(newLeads)
    }

    const leadsSubscription = supabase
      .channel("public:cqc_leads")
      .on("postgres_changes", { event: "*", schema: "public", table: "cqc_leads" }, refreshStats)
      .subscribe()

    const logsSubscription = supabase
      .channel("public:campaign_logs")
      .on("postgres_changes", { event: "*", schema: "public", table: "campaign_logs" }, refreshStats)
      .subscribe()

    const meetingsSubscription = supabase
      .channel("public:meetings")
      .on("postgres_changes", { event: "*", schema: "public", table: "meetings" }, refreshStats)
      .subscribe()

    return () => {
      supabase.removeChannel(leadsSubscription)
      supabase.removeChannel(logsSubscription)
      supabase.removeChannel(meetingsSubscription)
    }
  }, [])

  const filteredLeads = searchQuery
    ? recentLeads.filter(
        (l) =>
          l.company_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
          l.contact_first_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
          l.contact_last_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
          l.contact_email?.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : recentLeads

  return (
    <DashboardLayout>
        {/* Top Bar */}
        <header className="sticky top-[56px] md:top-0 z-30 border-b border-white/[0.06] bg-[#07090f]/80 backdrop-blur-2xl">
          <div className="flex items-center justify-between px-4 py-3 md:px-8 md:py-4">
            <div className="hidden sm:block">
              <h2 className="text-xl font-semibold text-white tracking-tight">Dashboard</h2>
              <p className="text-xs text-slate-500 mt-0.5">Real-time acquisition pipeline overview</p>
            </div>
            <div className="flex items-center gap-2 md:gap-4 w-full sm:w-auto">


              {/* Status badge */}
              <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                <PulseIndicator color="emerald" />
                <span className="text-xs font-medium text-emerald-400">Live</span>
              </div>

              {/* Time */}
              <div className="hidden md:flex items-center gap-2 text-xs text-slate-500">
                <Clock className="h-3 w-3" />
                <span>{lastUpdated.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" })}</span>
              </div>
            </div>
          </div>
        </header>

        <main className="px-4 py-6 md:px-8 md:py-8 space-y-6 md:space-y-8">

          {/* Metric Cards */}
          <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-7">
            <StatCard title="Prospects" value={totalLeads} subtitle="CQC Care Homes" icon={Users} gradient="bg-gradient-to-br from-emerald-500 to-teal-600" animate />
            <StatCard title="Verified" value={verifiedEmails} subtitle="Ready for outreach" icon={MailCheck} gradient="bg-gradient-to-br from-cyan-500 to-blue-600" animate />
            <StatCard title="Sent" value={emailsSent} subtitle="Emails dispatched" icon={Send} gradient="bg-gradient-to-br from-indigo-500 to-violet-600" animate />
            <StatCard title="Opened" value={openRate} subtitle="Opened emails" icon={BarChart3} gradient="bg-gradient-to-br from-violet-500 to-purple-600" animate />
            <StatCard title="Replies" value={replyRate} subtitle="Campaign replies" icon={Reply} gradient="bg-gradient-to-br from-blue-500 to-indigo-600" animate />
            <StatCard title="Interested" value={interestRate} subtitle="Positive responses" icon={ThumbsUp} gradient="bg-gradient-to-br from-emerald-500 to-green-600" animate />
            <StatCard title="Booked" value={meetingsBooked} subtitle="Meetings scheduled" icon={CalendarCheck} gradient="bg-gradient-to-br from-amber-500 to-orange-600" animate />
          </div>

          {/* Row 2: Chart + Funnel + Donut */}
          <div className="grid gap-6 grid-cols-1 lg:grid-cols-12">
            {/* Campaign Activity Chart */}
            <GlassPanel className="col-span-1 lg:col-span-5">
              <PanelHeader
                icon={Activity}
                iconBg="bg-indigo-500/10"
                iconColor="text-indigo-400"
                title="Campaign Activity"
                action={
                  <div className="flex items-center gap-4 text-xs">
                    <div className="flex items-center gap-1.5"><div className="h-2 w-2 rounded-full bg-indigo-400" /><span className="hidden sm:inline text-slate-400">Sent</span></div>
                    <div className="flex items-center gap-1.5"><div className="h-2 w-2 rounded-full bg-emerald-400" /><span className="hidden sm:inline text-slate-400">Opened</span></div>
                  </div>
                }
              />
              <div className="px-4 pb-6 overflow-x-auto">
                <div className="min-w-[400px]">
                  <ActivityChart data={chartData} />
                </div>
              </div>
            </GlassPanel>

            {/* Enrichment Funnel */}
            <GlassPanel className="col-span-1 lg:col-span-4">
              <PanelHeader
                icon={TrendingUp}
                iconBg="bg-cyan-500/10"
                iconColor="text-cyan-400"
                title="Enrichment Funnel"
                subtitle="Pipeline conversion"
              />
              <div className="px-4 md:px-6 pb-6 overflow-x-auto">
                <div className="min-w-[300px]">
                  <EnrichmentFunnel 
                    totalLeads={totalLeads} 
                    verifiedEmails={verifiedEmails} 
                    emailsSent={emailsSent}
                    positiveReplies={interestedCount}
                    meetingsBooked={meetingsBooked}
                  />
                </div>
              </div>
            </GlassPanel>

            {/* Status Breakdown Donut */}
            <GlassPanel className="col-span-1 lg:col-span-3">
              <PanelHeader
                icon={BarChart3}
                iconBg="bg-violet-500/10"
                iconColor="text-violet-400"
                title="Status Breakdown"
              />
              <div className="px-4 md:px-6 pb-6">
                <StatusBreakdown totalLeads={totalLeads} verifiedEmails={verifiedEmails} />
              </div>
            </GlassPanel>
          </div>

          {/* Row 3: Lead Pipeline + Activity Feed */}
          <div className="grid gap-6 grid-cols-1 lg:grid-cols-12">
            {/* Lead Pipeline Table */}
            <GlassPanel className="col-span-1 lg:col-span-8 flex flex-col">
              <PanelHeader
                icon={Users}
                iconBg="bg-emerald-500/10"
                iconColor="text-emerald-400"
                title="Lead Pipeline"
                subtitle={`${filteredLeads.length} contacts${searchQuery ? " (filtered)" : ""}`}
                action={
                  <button className="flex items-center gap-1 text-xs font-medium text-indigo-400 hover:text-indigo-300 transition-colors whitespace-nowrap">
                    View all <ChevronRight className="h-3 w-3" />
                  </button>
                }
              />
              <div className="flex-1 overflow-x-auto px-4 md:px-6 pb-6 max-h-[420px]">
                <div className="min-w-[800px]">
                  <LeadManager leads={filteredLeads || []} />
                </div>
              </div>
            </GlassPanel>

            {/* Live Activity Feed */}
            <GlassPanel className="col-span-1 lg:col-span-4 flex flex-col">
              <PanelHeader
                icon={Zap}
                iconBg="bg-amber-500/10"
                iconColor="text-amber-400"
                title="Live Activity"
                subtitle="Recent system events"
              />
              <div className="flex-1 overflow-y-auto px-4 pb-4 max-h-[420px]">
                <LiveActivityFeed leads={recentLeads} />
              </div>
            </GlassPanel>
          </div>
        </main>
    </DashboardLayout>
  )
}
