import { supabaseServer } from "@/lib/supabase-server"
import MeetingsClient from "./meetings-client"

export const dynamic = "force-dynamic"

export default async function MeetingsPage({
  searchParams,
}: {
  searchParams: Promise<{ page?: string; q?: string }>
}) {
  const resolvedParams = await searchParams
  const page = parseInt(resolvedParams.page || "1", 10)
  const q = resolvedParams.q || ""
  const perPage = 25

  // Fetch RPC intent counts
  const { data: metrics, error: rpcError } = await supabaseServer.rpc("get_meetings_metrics")
  if (rpcError) console.error("RPC Error:", rpcError)

  const upcomingCount = metrics?.upcoming || 0
  const pastCount = metrics?.past || 0

  let query = supabaseServer
    .from("meetings")
    .select("*", { count: "exact" })
    .order("start_time", { ascending: true })

  if (q) {
    query = query.or(`attendee_name.ilike.%${q}%,attendee_email.ilike.%${q}%`)
  }

  const { data: meetings, count, error } = await query.limit(1000)

  if (error) {
    console.error("Supabase error in MeetingsPage:", error)
  }
    
  return (
    <MeetingsClient 
      initialMeetings={meetings || []} 
      upcomingCount={upcomingCount}
      pastCount={pastCount}
      totalCount={count || 0}
    />
  )
}
