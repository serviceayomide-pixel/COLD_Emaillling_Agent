"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Send, MailOpen, Search, Mail, ArrowUpRight } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { supabase } from "@/lib/supabase"

type OutboxEmail = {
  id: number
  to: string
  toName: string
  company: string
  subject: string
  preview: string
  body: string
  sentAt: string
}

export default function OutboxClient({ 
  emails,
  totalSentCount,
  totalCount,
  currentPage,
  searchQuery: initialSearchQuery,
  perPage
}: { 
  emails: OutboxEmail[]
  totalSentCount: number
  totalCount: number
  currentPage: number
  searchQuery: string
  perPage: number
}) {
  const router = useRouter()
  const [selectedEmail, setSelectedEmail] = useState<number | null>(emails[0]?.id ?? null)
  const [searchQuery, setSearchQuery] = useState(initialSearchQuery)

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchQuery !== initialSearchQuery) {
        const params = new URLSearchParams()
        if (searchQuery) params.set("q", searchQuery)
        router.push(`/outbox?${params.toString()}`)
      }
    }, 400)
    return () => clearTimeout(timer)
  }, [searchQuery, initialSearchQuery, router])

  useEffect(() => {
    const sub = supabase
      .channel("outbox:messages")
      .on("postgres_changes", { event: "*", schema: "public", table: "outlook_messages" }, () => {
        router.refresh()
      })
      .subscribe()

    return () => {
      supabase.removeChannel(sub)
    }
  }, [router])

  const filteredEmails = emails
  const selected = emails.find((e) => e.id === selectedEmail) || emails[0]
  const totalPages = Math.ceil(totalCount / perPage)

  return (
    <>
      <header className="border-b border-white/[0.06] bg-[#07090f]/80 backdrop-blur-2xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between px-4 py-4 md:px-8 md:py-5 gap-4">
          <div>
            <h2 className="text-xl font-semibold text-white tracking-tight">Outbox</h2>
            <p className="text-xs text-slate-500 mt-0.5">Dispatched email outreach sequences</p>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-xs text-indigo-400 font-medium">
            <Send className="h-3.5 w-3.5" />
            Total Dispatched: <span className="font-bold text-white ml-1">{totalSentCount}</span>
          </div>
        </div>
      </header>

      <main className="flex flex-col md:flex-row h-[calc(100vh-[130px])] md:h-[calc(100vh-73px)]">
        {/* Email List */}
        <div className={`${selected ? "hidden md:flex" : "flex"} w-full md:w-[420px] border-r-0 md:border-r border-white/[0.06] flex-col h-full`}>
          <div className="p-4 border-b border-white/[0.06]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-500" />
              <input
                type="text"
                placeholder="Search outbox..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="h-9 w-full rounded-xl border border-white/[0.08] bg-white/[0.04] pl-9 pr-4 text-xs text-white placeholder:text-slate-600 focus:outline-none focus:border-indigo-500/40 transition-all"
              />
            </div>
          </div>
          <div className="flex-1 overflow-y-auto">
            {filteredEmails.length > 0 ? (
              filteredEmails.map((email) => {
                return (
                  <button
                    key={email.id}
                    onClick={() => setSelectedEmail(email.id)}
                    className={`w-full text-left p-4 border-b border-white/[0.04] transition-colors ${
                      selectedEmail === email.id ? "bg-indigo-500/5 border-l-2 border-l-indigo-500" : "hover:bg-white/[0.02]"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-slate-300">
                          {email.toName}
                        </span>
                      </div>
                      <span className="text-[10px] text-slate-600">{email.sentAt}</span>
                    </div>
                    <p className="text-xs text-slate-400 mb-1.5 truncate">{email.subject}</p>
                    <div className="flex items-center justify-between">
                      <p className="text-[11px] text-slate-600 truncate max-w-[280px]">{email.preview}</p>
                      <Badge variant="outline" className="bg-indigo-500/10 text-indigo-400 border-indigo-500/20 text-[9px] font-medium ml-2 flex-shrink-0 flex items-center gap-1">
                        Sent <ArrowUpRight className="h-2 w-2" />
                      </Badge>
                    </div>
                  </button>
                )
              })
            ) : (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <Send className="h-10 w-10 text-slate-700 mb-3" />
                <p className="text-sm text-slate-500 font-medium">No sent outreach yet</p>
                <p className="text-xs text-slate-600 mt-1">Dispatched emails to leads will appear here</p>
              </div>
            )}
          </div>
          
          {/* Pagination Controls */}
          {totalCount > 0 && (
            <div className="p-3 border-t border-white/[0.06] flex items-center justify-between bg-white/[0.01]">
              <span className="text-[10px] text-slate-500">
                {((currentPage - 1) * perPage) + 1}–{Math.min(currentPage * perPage, totalCount)} of {totalCount}
              </span>
              <div className="flex gap-1">
                <button
                  onClick={() => {
                    const params = new URLSearchParams()
                    if (searchQuery) params.set("q", searchQuery)
                    params.set("page", Math.max(1, currentPage - 1).toString())
                    router.push(`/outbox?${params.toString()}`)
                  }}
                  disabled={currentPage === 1}
                  className="px-2 py-1 rounded text-[10px] text-slate-400 hover:bg-white/[0.04] disabled:opacity-30 transition"
                >
                  Prev
                </button>
                <button
                  onClick={() => {
                    const params = new URLSearchParams()
                    if (searchQuery) params.set("q", searchQuery)
                    params.set("page", Math.min(totalPages, currentPage + 1).toString())
                    router.push(`/outbox?${params.toString()}`)
                  }}
                  disabled={currentPage >= totalPages}
                  className="px-2 py-1 rounded text-[10px] text-slate-400 hover:bg-white/[0.04] disabled:opacity-30 transition"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Email Detail */}
        <div className={`${!selected ? "hidden md:flex" : "flex"} flex-1 flex-col h-full bg-[#0a0d14]`}>
          {selected ? (
            <>
              <div className="p-4 md:p-6 border-b border-white/[0.06]">
                {/* Mobile Back Button */}
                <button 
                  onClick={() => setSelectedEmail(null)}
                  className="md:hidden flex items-center gap-2 text-xs font-medium text-slate-400 hover:text-white mb-4"
                >
                  Back to Outbox
                </button>
                
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
                  <h3 className="text-lg font-semibold text-white leading-tight">{selected.subject}</h3>
                  <Badge variant="outline" className="bg-indigo-500/10 text-indigo-400 border-indigo-500/20 text-xs font-medium self-start sm:self-auto flex items-center gap-1">
                    Outbox <Send className="h-2.5 w-2.5" />
                  </Badge>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex items-center justify-center h-9 w-9 rounded-xl bg-gradient-to-br from-indigo-500/20 to-violet-500/20 border border-indigo-500/10">
                    <span className="text-xs font-bold text-indigo-300">{selected.toName[0]}</span>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-200">{selected.toName}</p>
                    <p className="text-xs text-slate-500">To: {selected.to} &middot; {selected.company}</p>
                  </div>
                </div>
              </div>
              <div className="flex-1 p-4 md:p-6 overflow-y-auto">
                <div className="rounded-xl bg-white/[0.02] border border-white/[0.04] p-4 md:p-5">
                  <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap break-words">{selected.body}</p>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <MailOpen className="h-10 w-10 text-slate-700 mx-auto mb-3" />
                <p className="text-sm text-slate-500">Select an email to view</p>
              </div>
            </div>
          )}
        </div>
      </main>
    </>
  )
}
