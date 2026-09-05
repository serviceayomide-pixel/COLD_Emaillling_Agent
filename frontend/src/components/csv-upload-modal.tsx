"use client"

import { useState, useRef } from "react"
import { X, UploadCloud, AlertCircle, CheckCircle2, FileText, Loader2 } from "lucide-react"

export function CsvUploadModal({ isOpen, onClose, onUploadComplete }: { isOpen: boolean, onClose: () => void, onUploadComplete: () => void }) {
  const [file, setFile] = useState<File | null>(null)
  const [campaignName, setCampaignName] = useState("")
  const [dailyLimit, setDailyLimit] = useState<number>(200)
  const [customPrompt, setCustomPrompt] = useState<string>("")
  const [isValidating, setIsValidating] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [validationResult, setValidationResult] = useState<{ valid_count: number, warnings: string[] } | null>(null)
  
  const fileInputRef = useRef<HTMLInputElement>(null)

  if (!isOpen) return null;

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (!selectedFile) return
    
    setFile(selectedFile)
    setValidationResult(null)
    setIsValidating(true)
    
    const formData = new FormData()
    formData.append("file", selectedFile)
    formData.append("validate_only", "true")
    
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "https://backend-production-cba9a.up.railway.app"
      const res = await fetch(`${backendUrl}/api/upload-csv`, {
        method: "POST",
        body: formData,
      })
      const data = await res.json()
      if (res.ok) {
        setValidationResult(data)
      } else {
        alert("Validation failed: " + data.detail)
      }
    } catch (err) {
      console.error(err)
      alert("Error contacting server for validation")
    } finally {
      setIsValidating(false)
    }
  }

  const handleUpload = async () => {
    if (!file || !campaignName) return
    setIsUploading(true)
    
    const formData = new FormData()
    formData.append("file", file)
    formData.append("validate_only", "false")
    formData.append("campaign_name", campaignName)
    formData.append("daily_limit", dailyLimit.toString())
    if (customPrompt.trim()) {
      formData.append("custom_prompt", customPrompt)
    }
    
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "https://backend-production-cba9a.up.railway.app"
      const res = await fetch(`${backendUrl}/api/upload-csv`, {
        method: "POST",
        body: formData,
      })
      const data = await res.json()
      if (res.ok) {
        onUploadComplete()
        onClose()
        setFile(null)
        setCampaignName("")
        setValidationResult(null)
      } else {
        alert("Upload failed: " + data.detail)
      }
    } catch (err) {
      console.error(err)
      alert("Error contacting server for upload")
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="w-full max-w-2xl bg-[#0f111a] border border-white/10 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        <div className="flex items-center justify-between p-5 border-b border-white/10">
          <h2 className="text-xl font-semibold text-white">Upload New Leads</h2>
          <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-lg transition-colors">
            <X className="h-5 w-5 text-slate-400" />
          </button>
        </div>
        
        <div className="p-6 overflow-y-auto">
          {!file ? (
            <div 
              className="border-2 border-dashed border-white/10 rounded-xl p-10 flex flex-col items-center justify-center text-center cursor-pointer hover:border-indigo-500/50 hover:bg-indigo-500/5 transition-all"
              onClick={() => fileInputRef.current?.click()}
            >
              <input type="file" ref={fileInputRef} className="hidden" accept=".csv, .xlsx, .xls" onChange={handleFileChange} />
              <div className="h-16 w-16 bg-white/5 rounded-full flex items-center justify-center mb-4">
                <UploadCloud className="h-8 w-8 text-indigo-400" />
              </div>
              <h3 className="text-lg font-medium text-white mb-2">Click or drag CSV/Excel to upload</h3>
              <p className="text-sm text-slate-400 max-w-sm">
                Ensure your file has columns like "First Name", "Company Name", and "Email". 
                Missing emails will be flagged before upload.
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="flex items-center gap-4 p-4 rounded-xl border border-white/10 bg-white/5">
                <div className="h-12 w-12 bg-indigo-500/20 text-indigo-400 rounded-lg flex items-center justify-center">
                  <FileText className="h-6 w-6" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate">{file.name}</p>
                  <p className="text-xs text-slate-400">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
                <button 
                  onClick={() => { setFile(null); setValidationResult(null); }}
                  className="text-xs text-slate-400 hover:text-white underline"
                >
                  Change File
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Campaign Name</label>
                  <input 
                    type="text" 
                    value={campaignName}
                    onChange={(e) => setCampaignName(e.target.value)}
                    placeholder="e.g. Q3 Outreach"
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-slate-600 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Daily Email Limit (Across this campaign)</label>
                  <input 
                    type="number" 
                    min="1"
                    max="2000"
                    value={dailyLimit}
                    onChange={(e) => setDailyLimit(parseInt(e.target.value) || 200)}
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-slate-600 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="flex items-center justify-between text-sm font-medium text-slate-300 mb-2">
                  <span>Custom AI Prompt (Optional)</span>
                  <span className="text-xs text-slate-500">JSON constraints auto-applied</span>
                </label>
                <textarea 
                  value={customPrompt}
                  onChange={(e) => setCustomPrompt(e.target.value)}
                  placeholder="Override the master prompt for this specific campaign... (Leave blank for default)"
                  className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-slate-600 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 min-h-[100px] resize-y"
                />
              </div>

              {isValidating ? (
                <div className="flex items-center justify-center p-8 text-slate-400">
                  <Loader2 className="h-6 w-6 animate-spin mr-3 text-indigo-400" />
                  Validating file rows...
                </div>
              ) : validationResult && (
                <div className="space-y-4">
                  <div className="flex items-center gap-3 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                    <CheckCircle2 className="h-5 w-5 shrink-0" />
                    <div>
                      <p className="text-sm font-medium">{validationResult.valid_count} Valid Leads Found</p>
                      <p className="text-xs opacity-80">These leads have valid email addresses and will be imported.</p>
                    </div>
                  </div>

                  {validationResult.warnings.length > 0 && (
                    <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 max-h-48 overflow-y-auto">
                      <div className="flex items-center gap-2 mb-2">
                        <AlertCircle className="h-5 w-5 shrink-0" />
                        <p className="text-sm font-medium">{validationResult.warnings.length} Leads Missing Emails (Skipped)</p>
                      </div>
                      <ul className="text-xs space-y-1 opacity-80 list-disc list-inside">
                        {validationResult.warnings.map((w, i) => (
                          <li key={i}>{w}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
        
        <div className="p-5 border-t border-white/10 flex justify-end gap-3 bg-white/[0.02]">
          <button 
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-slate-300 hover:text-white transition-colors"
          >
            Cancel
          </button>
          <button 
            onClick={handleUpload}
            disabled={!file || !campaignName || !validationResult || validationResult.valid_count === 0 || isUploading}
            className="flex items-center px-6 py-2 rounded-lg bg-indigo-500 hover:bg-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium transition-colors"
          >
            {isUploading && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
            {isUploading ? "Importing..." : "Import Leads & Create Campaign"}
          </button>
        </div>
      </div>
    </div>
  )
}
