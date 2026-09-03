"use client"

import { useState } from "react"
import { Sidebar } from "@/components/sidebar"
import { Menu, Zap } from "lucide-react"
import { AutoLogout } from "@/components/auto-logout"

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <div className="flex min-h-screen">
      <AutoLogout />
      {/* Mobile Header (Only visible on small screens) */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-30 flex items-center justify-between px-4 py-3 border-b border-white/[0.06] bg-[#07090f]/90 backdrop-blur-xl">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center h-8 w-8 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 shadow-lg shadow-indigo-500/25">
            <Zap className="h-4 w-4 text-white" />
          </div>
          <h1 className="text-sm font-bold text-white tracking-tight leading-none">Acquisition Engine</h1>
        </div>
        <button 
          onClick={() => setMobileMenuOpen(true)}
          className="p-2 rounded-lg bg-white/[0.04] border border-white/[0.06] text-slate-300 hover:text-white hover:bg-white/[0.08]"
        >
          <Menu className="h-5 w-5" />
        </button>
      </div>

      <Sidebar mobileOpen={mobileMenuOpen} setMobileOpen={setMobileMenuOpen} />
      
      {/* 
        Main content wrapper: 
        - Mobile: no left margin (ml-0), add top padding for the mobile header (pt-16)
        - Desktop (md:): left margin matches sidebar width, no top padding 
      */}
      <div className="flex-1 w-full ml-0 pt-[60px] md:pt-0 md:ml-[240px] transition-all duration-300">
        {/* Animated Background Mesh */}
        <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
          <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-indigo-500/[0.03] rounded-full blur-[120px]" />
          <div className="absolute bottom-0 right-1/4 w-[400px] h-[400px] bg-violet-500/[0.03] rounded-full blur-[120px]" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-cyan-500/[0.02] rounded-full blur-[150px]" />
        </div>
        {children}
      </div>
    </div>
  )
}
