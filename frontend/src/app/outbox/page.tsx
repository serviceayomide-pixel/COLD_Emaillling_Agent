import { supabaseServer } from "@/lib/supabase-server"
import { DashboardLayout } from "@/components/dashboard-layout"
import OutboxClient from "./outbox-client"

export const dynamic = "force-dynamic"
export const revalidate = 0

export default async function OutboxPage({
  searchParams,
}: {
  searchParams: Promise<{ page?: string; q?: string }>
}) {
  const resolvedParams = await searchParams
  const page = parseInt(resolvedParams.page || "1", 10)
  const q = resolvedParams.q || ""
  const perPage = 25

  // Get active campaign month
  const { data: activeMonth } = await supabaseServer
    .from("campaign_months")
    .select("month_number")
    .eq("status", "active")
    .maybeSingle()

  const currentMonthNum = activeMonth?.month_number || 1

  // Fetch RPC intent counts
  const { data: metrics, error: rpcError } = await supabaseServer.rpc("get_outbox_metrics")
  if (rpcError) console.error("RPC Error:", rpcError)

  const totalSentCount = metrics?.total_sent || 0

  // Fetch messages from outlook_messages where folder is 'sentitems'
  let query = supabaseServer
    .from("outlook_messages")
    .select(`
      id,
      sender_email,
      recipient_email,
      subject,
      body,
      received_at,
      cqc_leads!inner (
        id,
        company_name,
        contact_first_name,
        contact_last_name,
        campaign_status,
        campaign_month
      )
    `, { count: "exact" })
    .eq("folder", "sentitems")
    .eq("cqc_leads.campaign_month", currentMonthNum)
    .order("received_at", { ascending: false })

  if (q) {
    query = query.or(`subject.ilike.%${q}%,recipient_email.ilike.%${q}%,cqc_leads.company_name.ilike.%${q}%`)
  }

  const from = (page - 1) * perPage
  const to = from + perPage - 1

  const { data: messages, count, error } = await query.range(from, to)

  if (error) {
    console.error("Supabase error in OutboxPage:", error)
  }

  const emails = (messages ?? []).map((msg: any) => {
    const lead = msg.cqc_leads ?? {}
    return {
      id: msg.id,
      to: msg.recipient_email ?? "unknown@company.co.uk",
      toName: [lead.contact_first_name, lead.contact_last_name].filter(Boolean).join(" ") || "Unknown",
      company: lead.company_name ?? "Unknown Company",
      subject: msg.subject ?? "Outreach",
      preview: msg.body ? msg.body.slice(0, 80) + "..." : "",
      body: msg.body ?? "",
      sentAt: msg.received_at
        ? new Date(msg.received_at).toLocaleString("en-GB", {
            day: "numeric",
            month: "short",
            hour: "2-digit",
            minute: "2-digit"
          })
        : "—",
    }
  })

  return (
    <DashboardLayout>
      <OutboxClient 
        emails={emails} 
        totalSentCount={totalSentCount} 
        totalCount={count || 0}
        currentPage={page}
        searchQuery={q}
        perPage={perPage}
      />
    </DashboardLayout>
  )
}
