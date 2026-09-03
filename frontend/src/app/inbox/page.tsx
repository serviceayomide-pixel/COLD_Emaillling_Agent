import { supabaseServer } from "@/lib/supabase-server"
import { DashboardLayout } from "@/components/dashboard-layout"
import InboxClient from "./inbox-client"

export const dynamic = "force-dynamic"

export default async function InboxPage({
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
  const { data: intentCounts, error: rpcError } = await supabaseServer.rpc("get_inbox_metrics")
  if (rpcError) console.error("RPC Error:", rpcError)

  // Fetch messages from outlook_messages where folder is 'inbox'
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
    .eq("folder", "inbox")
    .eq("cqc_leads.campaign_month", currentMonthNum)
    .order("received_at", { ascending: false })

  if (q) {
    query = query.or(`subject.ilike.%${q}%,sender_email.ilike.%${q}%,cqc_leads.company_name.ilike.%${q}%`)
  }

  const from = (page - 1) * perPage
  const to = from + perPage - 1

  const { data: messages, count, error } = await query.range(from, to)

  if (error) {
    console.error("Supabase error in InboxPage:", error)
  }

  const emails = (messages ?? []).map((msg: any) => {
    const lead = msg.cqc_leads ?? {}
    return {
      id: msg.id,
      from: msg.sender_email ?? "unknown@company.co.uk",
      fromName: [lead.contact_first_name, lead.contact_last_name].filter(Boolean).join(" ") || "Unknown",
      company: lead.company_name ?? "Unknown Company",
      subject: msg.subject ?? "Re: Outreach",
      preview: msg.body ? msg.body.slice(0, 80) + "..." : "",
      body: msg.body ?? "",
      intent: lead.campaign_status ?? "neutral",
      receivedAt: msg.received_at
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
      <InboxClient 
        emails={emails} 
        intentCounts={intentCounts || {}} 
        totalCount={count || 0}
        currentPage={page}
        searchQuery={q}
        perPage={perPage}
      />
    </DashboardLayout>
  )
}
