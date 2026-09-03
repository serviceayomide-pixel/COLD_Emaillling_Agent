"use client"

import { useEffect, useRef } from "react"
import { signOut } from "@/app/login/actions"
import { useRouter } from "next/navigation"

// 15 minutes in milliseconds
const TIMEOUT_MS = 15 * 60 * 1000

export function AutoLogout() {
  const router = useRouter()
  const timerRef = useRef<NodeJS.Timeout | null>(null)

  const resetTimer = () => {
    if (timerRef.current) clearTimeout(timerRef.current)
    timerRef.current = setTimeout(async () => {
      // User is idle, trigger sign out
      await signOut()
      // Fallback redirect just in case
      router.push("/login")
    }, TIMEOUT_MS)
  }

  useEffect(() => {
    // Initial timer setup
    resetTimer()

    // Events to track activity
    const events = [
      "mousemove",
      "mousedown",
      "keypress",
      "scroll",
      "touchmove",
      "click",
    ]

    const handleActivity = () => {
      resetTimer()
    }

    // Attach listeners
    events.forEach((event) => {
      window.addEventListener(event, handleActivity)
    })

    // Cleanup on unmount
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
      events.forEach((event) => {
        window.removeEventListener(event, handleActivity)
      })
    }
  }, [])

  // Render nothing as this is a purely logical component
  return null
}
