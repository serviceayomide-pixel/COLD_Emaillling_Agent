import { supabaseServer } from "@/lib/supabase-server"
import CampaignsClient from "./campaigns-client"

export const dynamic = "force-dynamic"

export default async function CampaignsPage() {
  const { data: months, error: monthsError } = await supabaseServer
    .from("campaign_months")
    .select("*")
    .order("month_number", { ascending: true })

  if (monthsError) {
    console.error("Error fetching campaign months:", monthsError)
  }

  const campaignMonths = months || []
  const campaignsList = []

  const { data: globalMetrics } = await supabaseServer.rpc('get_global_dashboard_metrics')

  for (const m of campaignMonths) {
    const { data: metrics } = await supabaseServer.rpc('get_campaign_month_metrics', { target_month: m.month_number })

    campaignsList.push({
      id: m.month_number,
      name: `Month ${m.month_number}`,
      status: m.status,
      leads: metrics?.leads || m.leads_count,
      sent: metrics?.sent || 0,
      opened: metrics?.opened || 0,
      replied: metrics?.replied || 0,
      startDate: m.start_date 
        ? new Date(m.start_date).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })
        : "Pending",
      endDate: m.end_date
        ? new Date(m.end_date).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })
        : "Pending",
    })
  }

  const totalLeads = globalMetrics?.total_leads || 0
  const activeCount = globalMetrics?.active_leads || 0
  const emailedCount = globalMetrics?.total_emails_sent || 0
  const repliedCount = globalMetrics?.total_replied_count || 0

  return (
    <CampaignsClient 
      initialCampaigns={campaignsList}
      totalLeadsCount={totalLeads || 0}
      activeLeadsCount={activeCount || 0}
      emailedLeadsCount={emailedCount || 0}
      repliedLeadsCount={repliedCount || 0}
    />
  )
}
