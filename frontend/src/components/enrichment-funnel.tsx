"use client"

import { Users, MailCheck, Send, ThumbsUp, CalendarCheck } from "lucide-react"

interface FunnelStage {
  label: string
  value: number
  icon: any
  color: string
  bgColor: string
  barColor: string
}

export function EnrichmentFunnel({
  totalLeads,
  verifiedEmails,
  emailsSent,
  positiveReplies,
  meetingsBooked,
}: {
  totalLeads: number
  verifiedEmails: number
  emailsSent: number
  positiveReplies: number
  meetingsBooked: number
}) {
  const stages: FunnelStage[] = [
    {
      label: "Prospects Sourced",
      value: totalLeads,
      icon: Users,
      color: "text-slate-300",
      bgColor: "bg-slate-500/10",
      barColor: "bg-gradient-to-r from-slate-500 to-slate-400",
    },
    {
      label: "Emails Verified",
      value: verifiedEmails,
      icon: MailCheck,
      color: "text-cyan-400",
      bgColor: "bg-cyan-500/10",
      barColor: "bg-gradient-to-r from-cyan-500 to-blue-500",
    },
    {
      label: "Emails Sent",
      value: emailsSent,
      icon: Send,
      color: "text-indigo-400",
      bgColor: "bg-indigo-500/10",
      barColor: "bg-gradient-to-r from-indigo-500 to-violet-500",
    },
    {
      label: "Positive Replies",
      value: positiveReplies,
      icon: ThumbsUp,
      color: "text-emerald-400",
      bgColor: "bg-emerald-500/10",
      barColor: "bg-gradient-to-r from-emerald-500 to-green-500",
    },
    {
      label: "Meetings Booked",
      value: meetingsBooked,
      icon: CalendarCheck,
      color: "text-amber-400",
      bgColor: "bg-amber-500/10",
      barColor: "bg-gradient-to-r from-amber-500 to-orange-500",
    },
  ]

  const maxValue = Math.max(...stages.map((s) => s.value), 1)

  return (
    <div className="space-y-3">
      {stages.map((stage, i) => {
        const percentage = maxValue > 0 ? (stage.value / maxValue) * 100 : 0
        const convRate =
          i > 0 && stages[i - 1].value > 0
            ? ((stage.value / stages[i - 1].value) * 100).toFixed(1)
            : null

        return (
          <div key={stage.label} className="group">
            <div className="flex items-center justify-between mb-1.5">
              <div className="flex items-center gap-2">
                <div className={`flex items-center justify-center h-6 w-6 rounded-lg ${stage.bgColor}`}>
                  <stage.icon className={`h-3 w-3 ${stage.color}`} />
                </div>
                <span className="text-xs font-medium text-slate-300">{stage.label}</span>
              </div>
              <div className="flex items-center gap-2">
                {convRate && (
                  <span className="text-[10px] font-medium text-slate-600 bg-white/[0.03] px-1.5 py-0.5 rounded">
                    {convRate}%
                  </span>
                )}
                <span className={`text-sm font-bold ${stage.color}`}>
                  {stage.value.toLocaleString()}
                </span>
              </div>
            </div>
            {/* Progress Bar */}
            <div className="h-2 w-full rounded-full bg-white/[0.04] overflow-hidden">
              <div
                className={`h-full rounded-full ${stage.barColor} transition-all duration-1000 ease-out`}
                style={{ width: `${Math.max(percentage, stage.value > 0 ? 3 : 0)}%` }}
              />
            </div>
            {/* Connector Line */}
            {i < stages.length - 1 && (
              <div className="flex justify-center py-1">
                <div className="w-px h-2 bg-white/[0.06]" />
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
