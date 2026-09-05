"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { DashboardLayout } from "@/components/dashboard-layout"
import { Send, Play, Pause, BarChart3, Mail, Clock, Users, Zap, UploadCloud } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { supabase } from "@/lib/supabase"
import { CsvUploadModal } from "@/components/csv-upload-modal"

const statusConfig: Record<string, { label: string; className: string; icon: any }> = {
  not_started: { label: "Draft", className: "bg-slate-500/10 text-slate-400 border-slate-500/20", icon: Clock },
  active: { label: "Active", className: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20", icon: Play },
  paused: { label: "Paused", className: "bg-amber-500/10 text-amber-400 border-amber-500/20", icon: Pause },
  completed: { label: "Completed", className: "bg-indigo-500/10 text-indigo-400 border-indigo-500/20", icon: BarChart3 },
  queued: { label: "Queued", className: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20", icon: Clock },
}

export default function CampaignsClient({ 
  initialCampaigns,
  totalLeadsCount,
  activeLeadsCount,
  emailedLeadsCount,
  repliedLeadsCount,
}: { 
  initialCampaigns: any[]
  totalLeadsCount: number
  activeLeadsCount: number
  emailedLeadsCount: number
  repliedLeadsCount: number
}) {
  const router = useRouter()
  const [updatingId, setUpdatingId] = useState<number | null>(null)
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false)
  
  // Local state so pause/resume is always instant and correct
  const [campaigns, setCampaigns] = useState<any[]>(initialCampaigns ?? [])

  // Sync if server re-renders with fresh data
  useEffect(() => {
    setCampaigns(initialCampaigns ?? [])
  }, [initialCampaigns])

  const handleToggleStatus = async (monthNumber: number, currentStatus: string) => {
    const newStatus = currentStatus === "active" ? "paused" : "active"

    // Optimistically update local state immediately so button flips instantly
    setCampaigns(prev =>
      prev.map(c => c.id === monthNumber ? { ...c, status: newStatus } : c)
    )
    setUpdatingId(monthNumber)

    const updatePayload: any = { status: newStatus }
    if (newStatus === "paused") {
      updatePayload.paused_at = new Date().toISOString()
    }

    const { error } = await supabase
      .from("campaign_months")
      .update(updatePayload)
      .eq("month_number", monthNumber)
    
    if (error) {
      console.error("Error updating campaign status:", error)
      alert(`Failed to ${newStatus === "paused" ? "pause" : "resume"} campaign: ${error.message}`)
      // Revert local state on error
      setCampaigns(prev =>
        prev.map(c => c.id === monthNumber ? { ...c, status: currentStatus } : c)
      )
    }
    setUpdatingId(null)
  }

  useEffect(() => {
    const leadsSub = supabase
      .channel("campaigns:leads")
      .on("postgres_changes", { event: "*", schema: "public", table: "cqc_leads" }, () => router.refresh())
      .subscribe()

    const logsSub = supabase
      .channel("campaigns:logs")
      .on("postgres_changes", { event: "*", schema: "public", table: "campaign_logs" }, () => router.refresh())
      .subscribe()

    const monthsSub = supabase
      .channel("campaigns:months")
      .on("postgres_changes", { event: "*", schema: "public", table: "campaign_months" }, () => router.refresh())
      .subscribe()

    return () => {
      supabase.removeChannel(leadsSub)
      supabase.removeChannel(logsSub)
      supabase.removeChannel(monthsSub)
    }
  }, [router])

  // Compute quick stats
  const totalLeads = totalLeadsCount
  const activeCount = activeLeadsCount
  const emailedCount = emailedLeadsCount
  const repliedCount = repliedLeadsCount


  return (
    <DashboardLayout>
      <header className="border-b border-white/[0.06] bg-[#07090f]/80 backdrop-blur-2xl">
        <div className="flex items-center justify-between px-4 py-4 md:px-8 md:py-5">
          <div>
            <h2 className="text-xl font-semibold text-white tracking-tight">Campaigns</h2>
            <p className="text-xs text-slate-500 mt-0.5">Manage your automated monthly outreach sequences</p>
          </div>
          <button 
            onClick={() => setIsUploadModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-500 hover:bg-indigo-600 text-white text-sm font-medium transition-colors"
          >
            <UploadCloud className="h-4 w-4" />
            Upload Leads
          </button>
        </div>
      </header>

      <main className="px-4 py-6 md:px-8 md:py-8 space-y-6">
        {/* Quick Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "Total Leads", value: totalLeads.toLocaleString(), icon: Users, gradient: "from-cyan-500 to-blue-600" },
            { label: "Active", value: activeCount.toLocaleString(), icon: Play, gradient: "from-emerald-500 to-teal-600" },
            { label: "Emailed", value: emailedCount.toLocaleString(), icon: Send, gradient: "from-indigo-500 to-violet-600" },
            { label: "Replied", value: repliedCount.toLocaleString(), icon: Mail, gradient: "from-violet-500 to-purple-600" },
          ].map((stat) => (
            <div key={stat.label} className="rounded-2xl border border-white/[0.06] bg-white/[0.03] backdrop-blur-xl p-5">
              <div className="flex items-center justify-between mb-3">
                <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">{stat.label}</span>
                <div className={`flex items-center justify-center h-8 w-8 rounded-lg bg-gradient-to-br ${stat.gradient}`}>
                  <stat.icon className="h-3.5 w-3.5 text-white" />
                </div>
              </div>
              <p className="text-2xl font-bold text-white">{stat.value}</p>
            </div>
          ))}
        </div>

        {/* Campaign Cards */}
        <div className="space-y-4">
          {campaigns.length > 0 ? (
            campaigns.map((campaign) => {
              const status = statusConfig[campaign.status] ?? statusConfig.not_started
              return (
                <div key={campaign.id} className="group rounded-2xl border border-white/[0.06] bg-white/[0.03] backdrop-blur-xl p-4 md:p-6 hover:border-white/[0.12] transition-all">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-5">
                    <div className="flex items-center gap-4">
                      <div className="flex items-center justify-center h-11 w-11 rounded-xl bg-gradient-to-br from-indigo-500/20 to-violet-500/20 border border-indigo-500/10">
                        <Send className="h-5 w-5 text-indigo-400" />
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-white tracking-tight">{campaign.name || `Month ${campaign.id}`}</h3>
                        <div className="flex items-center gap-3 mt-1">
                          <Badge variant="outline" className={`${status.className} text-[10px] font-medium`}>
                            <status.icon className="h-3 w-3 mr-1" />
                            {status.label}
                          </Badge>
                          <span className="text-xs text-slate-500">
                            Schedule: {campaign.startDate} &mdash; {campaign.endDate}
                          </span>
                        </div>
                      </div>
                    </div>
                    {(campaign.status === "active" || campaign.status === "paused" || campaign.status === "not_started" || campaign.status === "queued") && (
                      <button
                        onClick={() => handleToggleStatus(campaign.id, campaign.status)}
                        disabled={updatingId === campaign.id}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-semibold backdrop-blur-xl transition-all ${
                          campaign.status === "active"
                            ? "bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border-amber-500/20"
                            : "bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border-emerald-500/20"
                        } disabled:opacity-50`}
                      >
                        {updatingId === campaign.id ? (
                          <div className="h-3.5 w-3.5 animate-spin rounded-full border border-current border-t-transparent" />
                        ) : campaign.status === "active" ? (
                          <Pause className="h-3.5 w-3.5" />
                        ) : (
                          <Play className="h-3.5 w-3.5" />
                        )}
                        {updatingId === campaign.id
                          ? "Saving..."
                          : campaign.status === "active"
                          ? "Pause"
                          : "Play"}
                      </button>
                    )}
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 py-4 border-y border-white/[0.06] bg-white/[0.01] px-4 -mx-4 md:px-6 md:-mx-6">
                    <div>
                      <p className="text-[11px] text-slate-500 font-medium mb-1 uppercase tracking-wider">Leads</p>
                      <p className="text-xl font-semibold text-white">{campaign.leads}</p>
                    </div>
                    <div>
                      <p className="text-[11px] text-slate-500 font-medium mb-1 uppercase tracking-wider">Sent</p>
                      <p className="text-xl font-semibold text-white">{campaign.sent}</p>
                    </div>
                    <div>
                      <p className="text-[11px] text-slate-500 font-medium mb-1 uppercase tracking-wider">Opened</p>
                      <p className="text-xl font-semibold text-white">{campaign.opened}</p>
                    </div>
                    <div>
                      <p className="text-[11px] text-slate-500 font-medium mb-1 uppercase tracking-wider">Replied</p>
                      <p className="text-xl font-semibold text-white">{campaign.replied}</p>
                    </div>
                  </div>
                </div>
              )
            })
          ) : (
            <div className="flex flex-col items-center justify-center py-20 text-center rounded-2xl border border-white/[0.06] bg-white/[0.02] border-dashed">
              <Zap className="h-12 w-12 text-slate-700 mb-4" />
              <h3 className="text-lg font-medium text-slate-300">No Campaigns Yet</h3>
              <p className="text-sm text-slate-500 max-w-sm mt-2">
                Import CQC leads or trigger your first outreach sequence to see campaigns here.
              </p>
            </div>
          )}
        </div>
      </main>
      
      <CsvUploadModal 
        isOpen={isUploadModalOpen} 
        onClose={() => setIsUploadModalOpen(false)} 
        onUploadComplete={() => router.refresh()} 
      />
    </DashboardLayout>
  )
}
