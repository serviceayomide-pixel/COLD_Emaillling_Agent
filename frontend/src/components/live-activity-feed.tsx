"use client"

import { useEffect, useState } from "react"
import { MailCheck, UserPlus, Trash2, Zap, CheckCircle } from "lucide-react"

interface ActivityItem {
  id: number
  type: "enriched" | "verified" | "deleted" | "sent" | "booked"
  message: string
  time: string
}

const iconMap = {
  enriched: { icon: UserPlus, color: "text-cyan-400", bg: "bg-cyan-500/10" },
  verified: { icon: MailCheck, color: "text-emerald-400", bg: "bg-emerald-500/10" },
  deleted: { icon: Trash2, color: "text-red-400", bg: "bg-red-500/10" },
  sent: { icon: Zap, color: "text-indigo-400", bg: "bg-indigo-500/10" },
  booked: { icon: CheckCircle, color: "text-amber-400", bg: "bg-amber-500/10" },
}

export function LiveActivityFeed({ leads }: { leads: any[] }) {
  const [activities, setActivities] = useState<ActivityItem[]>([])

  useEffect(() => {
    // Generate activities from the most recent enriched leads
    if (leads && leads.length > 0) {
      const items: ActivityItem[] = leads.slice(0, 12).map((lead, i) => {
        const enrichedAt = lead.enriched_at ? new Date(lead.enriched_at) : new Date()
        const now = new Date()
        const diffMs = now.getTime() - enrichedAt.getTime()
        const diffMins = Math.floor(diffMs / 60000)
        const diffHours = Math.floor(diffMins / 60)
        const diffDays = Math.floor(diffHours / 24)

        let timeAgo = "just now"
        if (diffDays > 0) timeAgo = `${diffDays}d ago`
        else if (diffHours > 0) timeAgo = `${diffHours}h ago`
        else if (diffMins > 0) timeAgo = `${diffMins}m ago`

        return {
          id: lead.id || i,
          type: "verified" as const,
          message: `${lead.contact_first_name || "Contact"} ${lead.contact_last_name || ""} at ${lead.company_name || "Unknown"} verified`,
          time: timeAgo,
        }
      })
      setActivities(items)
    }
  }, [leads])

  if (activities.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <div className="flex items-center justify-center h-10 w-10 rounded-xl bg-slate-800/50 mb-3">
          <Zap className="h-4 w-4 text-slate-600" />
        </div>
        <p className="text-xs text-slate-500">No recent activity</p>
      </div>
    )
  }

  return (
    <div className="space-y-1">
      {activities.map((activity, i) => {
        const { icon: Icon, color, bg } = iconMap[activity.type]
        return (
          <div
            key={activity.id}
            className="flex items-start gap-3 p-2.5 rounded-xl hover:bg-white/[0.02] transition-colors duration-150"
            style={{ animationDelay: `${i * 50}ms` }}
          >
            <div className={`flex-shrink-0 flex items-center justify-center h-7 w-7 rounded-lg ${bg} mt-0.5`}>
              <Icon className={`h-3.5 w-3.5 ${color}`} />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs text-slate-300 leading-relaxed truncate">
                {activity.message}
              </p>
              <p className="text-[10px] text-slate-600 mt-0.5">{activity.time}</p>
            </div>
          </div>
        )
      })}
    </div>
  )
}
