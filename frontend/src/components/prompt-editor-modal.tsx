"use client"

import { useState, useEffect } from "react"
import { X, Loader2, Save, Undo2, Info } from "lucide-react"

interface PromptEditorModalProps {
  isOpen: boolean
  onClose: () => void
  campaignId: number
  campaignName: string
  currentPrompt: string | null
  onSave: () => void
}

const DEFAULT_GERMAN_PROMPT = `MASTER PROMPT
Hyper Personalized B2B Cold Email for German Industrial, Engineering, Manufacturing and Technology Companies

ROLE
Act as one of the world's best B2B enterprise cold email copywriters and research driven outbound strategists specializing in:
Industrial manufacturing, Engineering, Automation, Robotics, Machinery, Renewable energy, Semiconductor technology, Process technology, Industrial software, SaaS, Technical products, Engineering services, Production technology, Energy technology, Water technology, Advanced manufacturing.

RECIPIENT
Name: {contact_name}{job_title}
Company: {company_name}
Target Personas: Marketing Directors, Heads of Marketing, Leiter Marketing, Leiter Marketing und Kommunikation, Head of Marketing & Communications, Managing Directors.

CORE OBJECTIVE & POSITIONING
The objective is NOT to simply sell "3D animation".
The objective is to identify where the company's existing technical communication could become clearer, more engaging and easier to understand, then position technical visual storytelling as an additional communication layer that can help the company explain complex products, technologies, processes and engineering value.
You are essentially proposing:
"You already have the technical expertise and content. We can add a visual storytelling layer that makes the value easier to understand."

LANGUAGE REQUIREMENT
The final outreach emails MUST be written in natural, native German.
Do not translate English word for word.
Write the way a strong German B2B marketing professional would actually write to another German business professional.
The language should feel: Professional, Natural, Confident, Concise, Human, Specific, Business focused, Non promotional, Non robotic.
Avoid exaggerated sales language and American style sales expressions.
Avoid generic phrases such as "Ich hoffe, diese Nachricht erreicht Sie gut", "Ich wollte mich kurz vorstellen", "Wir sind eine fuehrende Animationsagentur".

CRITICAL FORMATTING RULE (ABSOLUTE)
DO NOT USE ANY HYPHENS OR DASHES IN THE FINAL EMAIL OUTPUT.
Zero hyphens. Zero en dashes. Zero em dashes. Zero dash bullet points.
Rewrite sentences naturally so that hyphens and dash characters are completely unnecessary.
Example: instead of "End to End", write "von Anfang bis Ende". Instead of "3D Animation", write "3D Visualisierung" or "Raeumliche Animation" without dashes. Instead of "60 bis 90 Sekunden", write "in einer Minute" or "innerhalb weniger Augenblicke".

RESEARCH DATA PROVIDED FOR THIS COMPANY:
[COMPANY WEBSITE CONTEXT]
{website_context}

[YOUTUBE CHANNEL AUDIT DATA]
{youtube_context}

EMAIL 1 (DAY 1 - INITIAL OUTREACH) REQUIREMENTS:
1. Conduct research based on the provided website and YouTube data.
2. Structure:
   - Paragraph 1: Specific observation about the company's product, technology, or current communication.
   - Paragraph 2: Communication insight (what live video or text shows vs what remains invisible like internal mechanics, fluid dynamics, flow of energy or data).
   - Paragraph 3: Visual opportunity (position visual storytelling as an additional layer, not a replacement).
   - Paragraph 4: Concrete visualization idea for one specific product or technology of {company_name}.
   - Paragraph 5: Low friction CTA (e.g. "Wenn das grundsaetzlich interessant ist, kann ich Ihnen gern einmal skizzieren, wie ich das fuer [Produkt] visuell aufbauen wuerde.").
3. Tone: Respectful, observant, professional, no hype, no hard sales pitch.

EMAIL 2 (DAY 3 - FOLLOW UP TOUCH) REQUIREMENTS:
1. Follow the "I took another look" principle (Der zweite Blick).
2. Do NOT say "Just following up", "Ich wollte nachfassen", or apologize for following up.
3. Keep it shorter (around 60 to 110 words in German).
4. Introduce a second angle or deepen the first thought (e.g. focusing on a specific internal process, trade fair / sales enablement use case, or cross section cutaway).
5. Very low friction CTA (e.g. offering a quick storyboard or visual sketch with no call required).
6. Must also strictly contain ZERO hyphens or dashes.`

export default function PromptEditorModal({ isOpen, onClose, campaignId, campaignName, currentPrompt, onSave }: PromptEditorModalProps) {
  const [prompt, setPrompt] = useState<string>("")
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    if (isOpen) {
      setPrompt(currentPrompt || DEFAULT_GERMAN_PROMPT)
    }
  }, [isOpen, currentPrompt])

  if (!isOpen) return null

  const handleSave = async () => {
    setIsSaving(true)
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "https://backend-production-cba9a.up.railway.app"
      const res = await fetch(`${backendUrl}/api/campaigns/${campaignId}/prompt`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ custom_prompt: prompt }),
      })
      if (!res.ok) throw new Error("Failed to save")
      onSave()
      onClose()
    } catch (err) {
      console.error(err)
      alert("Error saving custom prompt")
    } finally {
      setIsSaving(false)
    }
  }

  const handleReset = () => {
    if (confirm("Are you sure you want to reset to the default Master Prompt? Your current changes will be lost.")) {
      setPrompt(DEFAULT_GERMAN_PROMPT)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="w-full max-w-4xl bg-[#0f111a] border border-white/10 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[95vh]">
        <div className="flex items-center justify-between p-5 border-b border-white/10 bg-white/[0.02]">
          <div>
            <h2 className="text-xl font-semibold text-white">Edit Campaign Prompt</h2>
            <p className="text-sm text-slate-400 mt-1">Campaign: <span className="text-indigo-400">{campaignName}</span></p>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-lg transition-colors">
            <X className="h-5 w-5 text-slate-400" />
          </button>
        </div>
        
        <div className="flex-1 overflow-hidden flex flex-col p-6">
          <div className="flex items-center gap-2 p-3 mb-4 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400 text-sm">
            <Info className="h-5 w-5 shrink-0" />
            <p>
              <strong>Note:</strong> The strict JSON output formatting rules are automatically appended by the backend to prevent the app from crashing. You only need to define the creative rules, roles, and guidelines below.
            </p>
          </div>

          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            className="flex-1 w-full bg-black/40 border border-white/10 rounded-xl p-4 text-white placeholder:text-slate-600 font-mono text-sm leading-relaxed focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 resize-none min-h-[400px]"
            placeholder="Enter your custom AI prompt here..."
          />
        </div>
        
        <div className="p-5 border-t border-white/10 flex justify-between items-center bg-white/[0.02]">
          <button 
            onClick={handleReset}
            className="flex items-center px-4 py-2 text-sm font-medium text-slate-400 hover:text-amber-400 transition-colors"
          >
            <Undo2 className="h-4 w-4 mr-2" />
            Reset to Default
          </button>

          <div className="flex items-center gap-3">
            <button 
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-slate-300 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button 
              onClick={handleSave}
              disabled={isSaving}
              className="flex items-center px-6 py-2 rounded-lg bg-indigo-500 hover:bg-indigo-600 disabled:opacity-50 text-white text-sm font-medium transition-colors"
            >
              {isSaving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Save className="h-4 w-4 mr-2" />}
              {isSaving ? "Saving..." : "Save Prompt"}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
