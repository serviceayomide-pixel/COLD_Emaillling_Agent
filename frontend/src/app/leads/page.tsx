import { supabaseServer } from "@/lib/supabase-server"
import { LeadsPageClient } from "./leads-client"

export const dynamic = "force-dynamic"

export default async function LeadsPage({
  searchParams,
}: {
  searchParams: Promise<{ status?: string; q?: string; page?: string }>
}) {
  const resolvedParams = await searchParams
  const page = parseInt(resolvedParams.page || "1", 10)
  const perPage = 25
  const statusFilter = resolvedParams.status || "all"
  const q = resolvedParams.q || ""

  let query = supabaseServer
    .from("cqc_leads")
    .select("*", { count: "exact" })
    .order("enriched_at", { ascending: false, nullsFirst: false })

  if (statusFilter !== "all") {
    if (statusFilter === "pending") {
      query = query.or('enrichment_status.eq.pending,enrichment_status.is.null')
    } else {
      query = query.eq("enrichment_status", statusFilter)
    }
  }

  if (q) {
    query = query.or(`company_name.ilike.%${q}%,contact_first_name.ilike.%${q}%,contact_last_name.ilike.%${q}%,contact_email.ilike.%${q}%`)
  }

  const from = (page - 1) * perPage
  const to = from + perPage - 1

  const { data: leads, count: filteredCount } = await query.range(from, to)

  // Get status counts (unfiltered by search)
  const { count: globalTotalCount } = await supabaseServer
    .from("cqc_leads")
    .select("*", { count: "exact", head: true })

  const { count: enrichedCount } = await supabaseServer
    .from("cqc_leads")
    .select("*", { count: "exact", head: true })
    .eq("enrichment_status", "enriched")

  const { count: pendingCount } = await supabaseServer
    .from("cqc_leads")
    .select("*", { count: "exact", head: true })
    .or('enrichment_status.eq.pending,enrichment_status.is.null')

  return (
    <LeadsPageClient
      initialLeads={leads || []}
      totalCount={globalTotalCount || 0}
      filteredCount={filteredCount || 0}
      enrichedCount={enrichedCount || 0}
      pendingCount={pendingCount || 0}
      currentPage={page}
      searchQuery={q}
      statusFilter={statusFilter}
      perPage={perPage}
    />
  )
}
