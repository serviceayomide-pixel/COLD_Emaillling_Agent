"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { DashboardLayout } from "@/components/dashboard-layout"
import { Users, Search, Filter, Download, MailCheck, Clock, XCircle, Building2, ChevronLeft, ChevronRight } from "lucide-react"
import { Badge } from "@/components/ui/badge"

interface LeadsPageClientProps {
  initialLeads: any[]
  totalCount: number
  filteredCount: number
  enrichedCount: number
  pendingCount: number
  currentPage: number
  searchQuery: string
  statusFilter: string
  perPage: number
}

const statusConfig: Record<string, { label: string; className: string }> = {
  enriched: { label: "Verified", className: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" },
  pending: { label: "Pending", className: "bg-amber-500/10 text-amber-400 border-amber-500/20" },
  failed: { label: "Failed", className: "bg-red-500/10 text-red-400 border-red-500/20" },
  invalid: { label: "Invalid", className: "bg-slate-500/10 text-slate-400 border-slate-500/20" },
}

export function LeadsPageClient({ 
  initialLeads, 
  totalCount, 
  filteredCount,
  enrichedCount, 
  pendingCount,
  currentPage,
  searchQuery: initialSearchQuery,
  statusFilter,
  perPage
}: LeadsPageClientProps) {
  const router = useRouter()
  const [localSearch, setLocalSearch] = useState(initialSearchQuery)

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (localSearch !== initialSearchQuery) {
        updateFilters({ q: localSearch, page: 1 })
      }
    }, 400)
    return () => clearTimeout(timer)
  }, [localSearch, initialSearchQuery])

  const updateFilters = (updates: { q?: string; status?: string; page?: number }) => {
    const params = new URLSearchParams()
    
    const newQ = updates.q !== undefined ? updates.q : initialSearchQuery
    const newStatus = updates.status !== undefined ? updates.status : statusFilter
    const newPage = updates.page !== undefined ? updates.page : currentPage

    if (newQ) params.set("q", newQ)
    if (newStatus && newStatus !== "all") params.set("status", newStatus)
    if (newPage > 1) params.set("page", newPage.toString())

    router.push(`/leads?${params.toString()}`)
  }

  const totalPages = Math.ceil(filteredCount / perPage)

  return (
    <DashboardLayout>
      {/* Header */}
      <header className="border-b border-white/[0.06] bg-[#07090f]/80 backdrop-blur-2xl">
        <div className="flex items-center justify-between px-4 py-4 md:px-8 md:py-5">
          <div>
            <h2 className="text-xl font-semibold text-white tracking-tight">Leads</h2>
            <p className="text-xs text-slate-500 mt-0.5">{totalCount.toLocaleString()} total prospects in database</p>
          </div>
        </div>
      </header>

      <main className="px-4 py-6 md:px-8 md:py-8 space-y-4 md:space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="rounded-2xl border border-white/[0.06] bg-white/[0.03] backdrop-blur-xl p-5">
            <div className="flex items-center gap-3 mb-3">
              <div className="flex items-center justify-center h-8 w-8 rounded-lg bg-slate-500/10">
                <Users className="h-4 w-4 text-slate-400" />
              </div>
              <span className="text-xs font-medium text-slate-400 uppercase">Total Leads</span>
            </div>
            <p className="text-2xl font-bold text-white">{totalCount.toLocaleString()}</p>
          </div>
          <div className="rounded-2xl border border-white/[0.06] bg-white/[0.03] backdrop-blur-xl p-5">
            <div className="flex items-center gap-3 mb-3">
              <div className="flex items-center justify-center h-8 w-8 rounded-lg bg-emerald-500/10">
                <MailCheck className="h-4 w-4 text-emerald-400" />
              </div>
              <span className="text-xs font-medium text-slate-400 uppercase">Enriched</span>
            </div>
            <p className="text-2xl font-bold text-emerald-400">{enrichedCount.toLocaleString()}</p>
          </div>
          <div className="rounded-2xl border border-white/[0.06] bg-white/[0.03] backdrop-blur-xl p-5">
            <div className="flex items-center gap-3 mb-3">
              <div className="flex items-center justify-center h-8 w-8 rounded-lg bg-amber-500/10">
                <Clock className="h-4 w-4 text-amber-400" />
              </div>
              <span className="text-xs font-medium text-slate-400 uppercase">Pending</span>
            </div>
            <p className="text-2xl font-bold text-amber-400">{pendingCount.toLocaleString()}</p>
          </div>
        </div>

        {/* Filters Bar */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
          <div className="relative w-full sm:flex-1 sm:max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
            <input
              type="text"
              placeholder="Search by name, company, or email..."
              value={localSearch}
              onChange={(e) => setLocalSearch(e.target.value)}
              className="h-10 w-full rounded-xl border border-white/[0.08] bg-white/[0.04] pl-10 pr-4 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:border-indigo-500/40 transition-all"
            />
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Filter className="hidden sm:block h-4 w-4 text-slate-500 mr-1" />
            {["all", "enriched", "pending", "failed"].map((status) => (
              <button
                key={status}
                onClick={() => updateFilters({ status, page: 1 })}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                  statusFilter === status
                    ? "bg-indigo-500/15 text-indigo-400 border border-indigo-500/30"
                    : "bg-white/[0.04] text-slate-400 border border-white/[0.06] hover:bg-white/[0.08]"
                }`}
              >
                {status === "all" ? "All" : status.charAt(0).toUpperCase() + status.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Table */}
        <div className="rounded-2xl border border-white/[0.06] bg-white/[0.03] backdrop-blur-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[800px]">
              <thead>
                <tr className="border-b border-white/[0.06]">
                  <th className="text-left text-[11px] font-semibold text-slate-500 uppercase tracking-wider px-5 py-3">Contact</th>
                  <th className="text-left text-[11px] font-semibold text-slate-500 uppercase tracking-wider px-5 py-3">Company</th>
                  <th className="text-left text-[11px] font-semibold text-slate-500 uppercase tracking-wider px-5 py-3">Email</th>
                  <th className="text-left text-[11px] font-semibold text-slate-500 uppercase tracking-wider px-5 py-3">Status</th>
                  <th className="text-left text-[11px] font-semibold text-slate-500 uppercase tracking-wider px-5 py-3">Enriched</th>
                </tr>
              </thead>
              <tbody>
                {initialLeads.map((lead) => {
                  const status = statusConfig[lead.enrichment_status] || statusConfig.pending
                  return (
                    <tr key={lead.id} className="border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors">
                      <td className="px-5 py-3.5">
                        <div className="flex items-center gap-3">
                          <div className="flex-shrink-0 flex items-center justify-center h-8 w-8 rounded-lg bg-gradient-to-br from-indigo-500/20 to-violet-500/20 border border-indigo-500/10">
                            <span className="text-xs font-bold text-indigo-300">
                              {(lead.contact_first_name?.[0] || "?").toUpperCase()}
                            </span>
                          </div>
                          <span className="text-sm font-medium text-slate-200">
                            {lead.contact_first_name || "—"} {lead.contact_last_name || ""}
                          </span>
                        </div>
                      </td>
                      <td className="px-5 py-3.5">
                        <div className="flex items-center gap-2">
                          <Building2 className="h-3.5 w-3.5 text-slate-600 flex-shrink-0" />
                          <span className="text-sm text-slate-300 truncate max-w-[200px]">{lead.company_name || "—"}</span>
                        </div>
                      </td>
                      <td className="px-5 py-3.5">
                        <span className="text-sm text-slate-400 font-mono">{lead.contact_email || "—"}</span>
                      </td>
                      <td className="px-5 py-3.5">
                        <Badge variant="outline" className={`${status.className} text-[10px] font-medium`}>
                          {status.label}
                        </Badge>
                      </td>
                      <td className="px-5 py-3.5">
                        <span className="text-xs text-slate-500">
                          {lead.enriched_at ? new Date(lead.enriched_at).toLocaleDateString("en-GB") : "—"}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between px-5 py-3 border-t border-white/[0.06]">
            <span className="text-xs text-slate-500">
              Showing {filteredCount === 0 ? 0 : ((currentPage - 1) * perPage) + 1}–{Math.min(currentPage * perPage, filteredCount)} of {filteredCount}
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => updateFilters({ page: Math.max(1, currentPage - 1) })}
                disabled={currentPage === 1}
                className="flex items-center justify-center h-8 w-8 rounded-lg border border-white/[0.08] bg-white/[0.04] text-slate-400 hover:bg-white/[0.08] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <span className="text-xs text-slate-400 px-2">
                Page {currentPage} of {totalPages || 1}
              </span>
              <button
                onClick={() => updateFilters({ page: Math.min(totalPages, currentPage + 1) })}
                disabled={currentPage >= totalPages}
                className="flex items-center justify-center h-8 w-8 rounded-lg border border-white/[0.08] bg-white/[0.04] text-slate-400 hover:bg-white/[0.08] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </main>
    </DashboardLayout>
  )
}
