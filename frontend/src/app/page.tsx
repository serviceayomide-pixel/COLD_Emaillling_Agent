import { supabaseServer } from "@/lib/supabase-server"
import { DashboardClient } from "@/components/dashboard-client"

export const dynamic = 'force-dynamic' // Ensure page is not statically cached
export const revalidate = 0

export default async function Dashboard() {
  // 1. Fetch the active campaign month
  const { data: activeMonthData } = await supabaseServer
    .from("campaign_months")
    .select("month_number")
    .eq("status", "active")
    .maybeSingle()

  const activeMonth = activeMonthData?.month_number || 1

  // 2. Fetch live metrics via RPC
  const { data: metrics, error } = await supabaseServer.rpc('get_global_dashboard_metrics')
  if (error) console.error("Error fetching dashboard metrics:", error)

  // Fetch first 50 enriched leads for the UI table (global recent)
  const { data: recentLeads } = await supabaseServer.from('cqc_leads')
    .select('*')
    .eq('enrichment_status', 'enriched')
    .order('enriched_at', { ascending: false })
    .limit(50)

  const sent = metrics?.total_emails_sent || 0
  const opened = metrics?.total_emails_opened || 0
  const replied = metrics?.total_replied_count || 0
  const interested = metrics?.total_interested_count || 0

  return (
    <DashboardClient 
      initialTotalLeads={metrics?.total_leads || 0}
      initialVerifiedEmails={metrics?.verified_leads || 0}
      initialRecentLeads={recentLeads || []}
      initialEmailsSent={sent}
      initialOpenRate={opened} 
      initialReplyRate={replied} 
      initialInterestRate={interested} 
      initialMeetingsBooked={metrics?.meetings_booked || 0}
      initialInterestedCount={interested}
      initialChartData={metrics?.chart_data || []}
      activeMonthNumber={activeMonth}
    />
  )
}
