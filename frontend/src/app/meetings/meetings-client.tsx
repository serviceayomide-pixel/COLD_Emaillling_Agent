"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { DashboardLayout } from "@/components/dashboard-layout"
import { CalendarCheck, Clock, Video, MapPin, User, ChevronLeft, ChevronRight } from "lucide-react"
import { supabase } from "@/lib/supabase"

const daysOfWeek = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
const monthsOfYear = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December"
]

function getDaysInMonth(year: number, month: number) {
  const days = []
  const date = new Date(year, month, 1)
  let startDay = date.getDay()
  let offset = startDay === 0 ? 6 : startDay - 1
  for (let i = 0; i < offset; i++) {
    days.push({ day: 0, hasEvent: false, blank: true })
  }
  const numDays = new Date(year, month + 1, 0).getDate()
  for (let i = 1; i <= numDays; i++) {
    days.push({ day: i, hasEvent: false, blank: false })
  }
  return days
}

export default function MeetingsClient({ 
  initialMeetings,
  upcomingCount,
  pastCount,
  totalCount
}: { 
  initialMeetings: any[]
  upcomingCount: number
  pastCount: number
  totalCount: number
}) {
  const router = useRouter()
  const [currentDate, setCurrentDate] = useState(new Date())

  useEffect(() => {
    const sub = supabase
      .channel("meetings:all")
      .on("postgres_changes", { event: "*", schema: "public", table: "meetings" }, () => {
        router.refresh()
      })
      .subscribe()

    return () => {
      supabase.removeChannel(sub)
    }
  }, [router])

  const handlePrevMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1))
  }

  const handleNextMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1))
  }

  const totalBooked = totalCount
  const completed = pastCount
  
  const now = new Date()
  const oneWeek = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000)
  const thisWeek = initialMeetings.filter(m => {
    if (!m.start_time) return false
    const st = new Date(m.start_time)
    return st >= now && st <= oneWeek
  }).length
  
  const upcomingMeetings = initialMeetings.filter(m => {
    if (!m.start_time) return false
    const st = new Date(m.start_time)
    return st >= now
  })

  const activeYear = currentDate.getFullYear()
  const activeMonth = currentDate.getMonth()
  const monthName = monthsOfYear[activeMonth]
  
  const calendarDays = getDaysInMonth(activeYear, activeMonth).map(d => {
    if (d.blank) return d
    const hasMeeting = initialMeetings.some(m => {
      if (!m.start_time) return false
      const st = new Date(m.start_time)
      return st.getFullYear() === activeYear &&
             st.getMonth() === activeMonth &&
             st.getDate() === d.day
    })
    return { ...d, hasEvent: hasMeeting }
  })

  const isCurrentMonth = now.getFullYear() === activeYear && now.getMonth() === activeMonth
  const todayDay = now.getDate()

  return (
    <DashboardLayout>
      <header className="border-b border-white/[0.06] bg-[#07090f]/80 backdrop-blur-2xl">
        <div className="flex items-center justify-between px-4 py-4 md:px-8 md:py-5">
          <div>
            <h2 className="text-xl font-semibold text-white tracking-tight">Meetings</h2>
            <p className="text-xs text-slate-500 mt-0.5">Calendar bookings via Cal.com + Microsoft Exchange</p>
          </div>
        </div>
      </header>

      <main className="px-4 py-6 md:px-8 md:py-8 space-y-6">
        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: "Total Booked", value: totalBooked.toString(), icon: CalendarCheck, gradient: "from-indigo-500 to-violet-600" },
            { label: "This Week", value: thisWeek.toString(), icon: Clock, gradient: "from-cyan-500 to-blue-600" },
            { label: "Completed", value: completed.toString(), icon: Video, gradient: "from-emerald-500 to-teal-600" },
            { label: "Attended", value: completed.toString(), icon: User, gradient: "from-amber-500 to-orange-600" },
          ].map((stat) => (
            <div key={stat.label} className="rounded-2xl border border-white/[0.06] bg-white/[0.03] backdrop-blur-xl p-4 md:p-5">
              <div className="flex items-center justify-between mb-3">
                <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">{stat.label}</span>
                <div className={`flex items-center justify-center h-8 w-8 rounded-lg bg-gradient-to-br ${stat.gradient}`}>
                  <stat.icon className="h-3.5 w-3.5 text-white" />
                </div>
              </div>
              <p className="text-2xl font-bold text-white">{stat.value}</p>
            </div>
          ))}
        </div>

        <div className="grid gap-6 grid-cols-1 lg:grid-cols-12">
          {/* Calendar Widget */}
          <div className="col-span-1 lg:col-span-7 rounded-2xl border border-white/[0.06] bg-white/[0.03] backdrop-blur-xl">
            <div className="p-6 pb-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex items-center justify-center h-8 w-8 rounded-lg bg-indigo-500/10">
                  <CalendarCheck className="h-4 w-4 text-indigo-400" />
                </div>
                <h3 className="text-base font-semibold text-white">{monthName} {activeYear}</h3>
              </div>
              <div className="flex items-center gap-2">
                <button 
                  onClick={handlePrevMonth}
                  className="flex items-center justify-center h-7 w-7 rounded-lg border border-white/[0.08] bg-white/[0.04] text-slate-400 hover:bg-white/[0.08] hover:text-white transition-colors"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <button 
                  onClick={handleNextMonth}
                  className="flex items-center justify-center h-7 w-7 rounded-lg border border-white/[0.08] bg-white/[0.04] text-slate-400 hover:bg-white/[0.08] hover:text-white transition-colors"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
            <div className="px-6 pb-6">
              <div className="grid grid-cols-7 mb-2">
                {daysOfWeek.map((day) => (
                  <div key={day} className="text-center text-[10px] font-semibold text-slate-600 uppercase tracking-wider py-2">
                    {day}
                  </div>
                ))}
              </div>
              <div className="grid grid-cols-7 gap-1">
                {calendarDays.map((d, idx) => {
                  if (d.blank) {
                    return <div key={`blank-${idx}`} className="h-12" />
                  }
                  const isToday = isCurrentMonth && d.day === todayDay
                  return (
                    <button
                      key={d.day}
                      className={`relative h-12 rounded-lg text-sm font-medium transition-all hover:bg-white/[0.04] ${
                        isToday
                          ? "bg-indigo-500/15 text-indigo-400 border border-indigo-500/30"
                          : "text-slate-300"
                      }`}
                    >
                      {d.day}
                      {d.hasEvent && (
                        <div className="absolute bottom-1.5 left-1/2 -translate-x-1/2 h-1 w-1 rounded-full bg-indigo-400" />
                      )}
                    </button>
                  )
                })}
              </div>
            </div>
          </div>

          {/* Upcoming Meetings */}
          <div className="lg:col-span-5 rounded-2xl border border-white/[0.06] bg-white/[0.03] backdrop-blur-xl flex flex-col">
            <div className="p-6 pb-4">
              <div className="flex items-center gap-3">
                <div className="flex items-center justify-center h-8 w-8 rounded-lg bg-emerald-500/10">
                  <Clock className="h-4 w-4 text-emerald-400" />
                </div>
                <div>
                  <h3 className="text-base font-semibold text-white">Upcoming</h3>
                  <p className="text-xs text-slate-500">Next 7 days</p>
                </div>
              </div>
            </div>
            <div className="flex-1 px-6 pb-6 flex flex-col">
              {upcomingMeetings.length === 0 ? (
                <div className="flex-1 flex flex-col items-center justify-center text-center py-8">
                  <CalendarCheck className="h-10 w-10 text-slate-700 mx-auto mb-3" />
                  <p className="text-sm text-slate-500 font-medium">No meetings scheduled</p>
                  <p className="text-xs text-slate-600 mt-1 max-w-[260px]">
                    Meetings will appear here when prospects book via Cal.com
                  </p>
                </div>
              ) : (
                <div className="space-y-3 mt-2">
                  {upcomingMeetings.map(m => (
                    <div key={m.id} className="flex items-center justify-between p-3 rounded-xl border border-white/[0.04] bg-white/[0.02]">
                      <div>
                        <p className="text-sm font-medium text-white">{m.attendee_name || m.attendee_email}</p>
                        <p className="text-xs text-slate-400">{m.start_time ? new Date(m.start_time).toLocaleString('en-US', { timeZone: 'Europe/London' }) : ''}</p>
                      </div>
                      {m.meeting_url && (
                        <a href={m.meeting_url} target="_blank" rel="noopener noreferrer" className="text-xs text-indigo-400 hover:text-indigo-300">
                          Join Call
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </DashboardLayout>
  )
}
