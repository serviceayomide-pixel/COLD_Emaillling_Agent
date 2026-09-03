"use client"

import { useState, useEffect } from "react"
import { usePathname } from "next/navigation"
import Link from "next/link"
import {
  LayoutDashboard,
  Users,
  Send,
  CalendarCheck,
  Zap,
  ChevronLeft,
  ChevronRight,
  BarChart3,
  Inbox,
  LogOut,
  X,
  Mail,
} from "lucide-react"

import { signOut } from "@/app/login/actions"

const navItems = [
  { label: "Dashboard", href: "/", icon: LayoutDashboard },
  { label: "Leads", href: "/leads", icon: Users },
  { label: "Campaigns", href: "/campaigns", icon: Send },
  { label: "Inbox", href: "/inbox", icon: Inbox },
  { label: "Outbox", href: "/outbox", icon: Mail },
  { label: "Analytics", href: "/analytics", icon: BarChart3 },
  { label: "Meetings", href: "/meetings", icon: CalendarCheck },
]

export function Sidebar({ mobileOpen = false, setMobileOpen }: { mobileOpen?: boolean, setMobileOpen?: (open: boolean) => void }) {
  const [collapsed, setCollapsed] = useState(false)
  const pathname = usePathname()

  // Close mobile menu when route changes
  useEffect(() => {
    if (mobileOpen && setMobileOpen) {
      setMobileOpen(false)
    }
  }, [pathname])

  return (
    <>
      {/* Mobile Backdrop overlay */}
      {mobileOpen && (
        <div 
          className="md:hidden fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"
          onClick={() => setMobileOpen && setMobileOpen(false)}
        />
      )}

      <aside
        className={`fixed top-0 left-0 z-50 h-screen flex flex-col border-r border-white/[0.06] bg-[#0a0d14]/95 backdrop-blur-2xl transition-transform duration-300 ${
          collapsed ? "w-[72px]" : "w-[240px]"
        } 
        /* Mobile transform classes */
        ${mobileOpen ? "translate-x-0" : "-translate-x-full"}
        /* Desktop transform classes */
        md:translate-x-0
        `}
      >
        {/* Logo Area */}
        <div className={`flex items-center gap-3 px-4 py-5 border-b border-white/[0.06] ${collapsed ? "justify-center" : ""}`}>
          <div className="flex-shrink-0 flex items-center justify-center h-9 w-9 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 shadow-lg shadow-indigo-500/25">
            <Zap className="h-4 w-4 text-white" />
          </div>
          {!collapsed && (
            <div className="flex-1 overflow-hidden">
              <h1 className="text-sm font-bold text-white tracking-tight leading-none">Acquisition</h1>
              <p className="text-[10px] text-slate-500 font-medium mt-0.5">ENGINE v1.4</p>
            </div>
          )}
          {/* Mobile close button */}
          {!collapsed && setMobileOpen && (
            <button 
              className="md:hidden p-1.5 text-slate-400 hover:text-white bg-white/[0.04] rounded-lg"
              onClick={() => setMobileOpen(false)}
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        {/* Nav Items */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {!collapsed && (
            <p className="text-[10px] font-semibold text-slate-600 uppercase tracking-widest px-3 mb-3">
              Main Menu
            </p>
          )}
          {navItems.map((item) => {
            const isActive = pathname === item.href
            return (
              <Link
                key={item.label}
                href={item.href}
                className={`group flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? "bg-indigo-500/10 text-indigo-400 border border-indigo-500/20"
                    : "text-slate-400 hover:text-white hover:bg-white/[0.04] border border-transparent"
                } ${collapsed ? "justify-center" : ""}`}
              >
                <item.icon className={`h-[18px] w-[18px] flex-shrink-0 ${isActive ? "text-indigo-400" : "text-slate-500 group-hover:text-slate-300"}`} />
                {!collapsed && <span>{item.label}</span>}
                {isActive && !collapsed && (
                  <div className="ml-auto h-1.5 w-1.5 rounded-full bg-indigo-400" />
                )}
              </Link>
            )
          })}
        </nav>

        {/* Bottom Items */}
        <div className="px-3 py-3 border-t border-white/[0.06] space-y-1">
          {/* Logout Button */}
          <button
            onClick={() => signOut()}
            className={`group flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-400 hover:text-white hover:bg-red-500/10 hover:text-red-400 transition-all duration-200 w-full ${collapsed ? "justify-center" : ""}`}
          >
            <LogOut className="h-[18px] w-[18px] flex-shrink-0 text-slate-500 group-hover:text-red-400" />
            {!collapsed && <span>Log out</span>}
          </button>

          {/* Collapse Toggle (Hidden on mobile because it's always full width there) */}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className={`hidden md:flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-500 hover:text-white hover:bg-white/[0.04] transition-all duration-200 w-full ${collapsed ? "justify-center" : ""}`}
          >
            {collapsed ? (
              <ChevronRight className="h-[18px] w-[18px]" />
            ) : (
              <>
                <ChevronLeft className="h-[18px] w-[18px]" />
                <span>Collapse</span>
              </>
            )}
          </button>
        </div>
      </aside>
    </>
  )
}
