import { supabaseServer } from "@/lib/supabase-server"
import { DashboardLayout } from "@/components/dashboard-layout"
import AnalyticsClient from "./analytics-client"

export const dynamic = "force-dynamic"

export default async function AnalyticsPage() {
  const { data: metrics, error } = await supabaseServer.rpc('get_analytics_metrics')
  if (error) console.error("Error fetching analytics metrics:", error)

  const totalLeads = metrics?.total_leads || 0
  const emailedLeads = metrics?.emailed_leads || 0
  const repliedLeads = metrics?.replied_leads || 0
  
  const positiveRepliedLeads = metrics?.positive_replied_leads || 0
  const enrichedLeads = metrics?.enriched_leads || 0

  // Format as counts per user request
  const replyRate = repliedLeads.toString()
  const positiveRate = positiveRepliedLeads.toString()

  const chartData = metrics?.chart_data && metrics.chart_data.length > 0
    ? metrics.chart_data
    : [
        { week: "Week 1", sent: 0, opened: 0, replied: 0 },
        { week: "Week 2", sent: 0, opened: 0, replied: 0 },
        { week: "Week 3", sent: 0, opened: 0, replied: 0 },
        { week: "Week 4", sent: 0, opened: 0, replied: 0 },
      ]

  const enrichedPercent = totalLeads > 0 ? Math.round((enrichedLeads / totalLeads) * 100) : 0
  const notEnrichedPercent = 100 - enrichedPercent

  const topSubjects = metrics?.top_subjects || []

  return (
    <DashboardLayout>
      <AnalyticsClient
        totalLeads={totalLeads}
        emailedLeads={emailedLeads}
        repliedLeads={repliedLeads}
        replyRate={replyRate}
        positiveRate={positiveRate}
        chartData={chartData}
        enrichedPercent={enrichedPercent}
        notEnrichedPercent={notEnrichedPercent}
        topSubjects={topSubjects}
      />
    </DashboardLayout>
  )
}
