import { Badge } from "@/components/ui/badge"
import { MailCheck, Building2, User } from "lucide-react"

export function LeadManager({ leads }: { leads: any[] }) {
  if (!leads || leads.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="flex items-center justify-center h-12 w-12 rounded-2xl bg-slate-800/50 mb-4">
          <User className="h-5 w-5 text-slate-500" />
        </div>
        <p className="text-sm text-slate-400 font-medium">No enriched leads yet</p>
        <p className="text-xs text-slate-600 mt-1">Leads will appear here after enrichment</p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {leads.map((lead) => (
        <div
          key={lead.id}
          className="group flex items-center gap-3 p-3 rounded-xl border border-transparent hover:border-white/[0.06] hover:bg-white/[0.03] transition-all duration-200 cursor-default"
        >
          {/* Avatar */}
          <div className="flex-shrink-0 flex items-center justify-center h-9 w-9 rounded-xl bg-gradient-to-br from-indigo-500/20 to-violet-500/20 border border-indigo-500/10">
            <span className="text-xs font-bold text-indigo-300">
              {(lead.contact_first_name?.[0] || "?").toUpperCase()}
            </span>
          </div>

          {/* Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <p className="text-sm font-medium text-slate-200 truncate">
                {lead.contact_first_name} {lead.contact_last_name}
              </p>
              <Badge className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20 text-[10px] px-1.5 py-0 font-medium hover:bg-emerald-500/10">
                Ready
              </Badge>
            </div>
            <div className="flex items-center gap-3 mt-0.5">
              <span className="flex items-center gap-1 text-xs text-slate-500 truncate">
                <Building2 className="h-3 w-3 flex-shrink-0" />
                {lead.company_name}
              </span>
              {lead.contact_email && (
                <span className="flex items-center gap-1 text-xs text-slate-500 truncate">
                  <MailCheck className="h-3 w-3 flex-shrink-0" />
                  {lead.contact_email}
                </span>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
