"use client"
import clsx from "clsx"
import type React from "react"

import { useRef, useState, useCallback } from "react"
import { Upload, FileText, Download, X } from "lucide-react"

type ExtractionResult = {
  filename: string
  requirements: Record<string, unknown>[]
  summary: {
    total: number
    with_tests: number
    with_guidance: number
    total_tests: number
  }
}

type State = "idle" | "uploading" | "processing" | "success" | "error"

export function PdfUploadForm() {
  const [state, setState] = useState<State>("idle")
  const [error, setError] = useState<string>()
  const [result, setResult] = useState<ExtractionResult | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFiles = useCallback(async (files: FileList | null) => {
    if (!files || files.length === 0) return

    const file = files[0]
    if (file.type !== "application/pdf") {
      setError("Veuillez sélectionner un fichier PDF valide")
      setState("error")
      setTimeout(() => {
        setError(undefined)
        setState("idle")
      }, 3000)
      return
    }

    if (file.size > 50 * 1024 * 1024) {
      setError("Le fichier est trop volumineux (max 50MB)")
      setState("error")
      setTimeout(() => {
        setError(undefined)
        setState("idle")
      }, 3000)
      return
    }

    try {
      setState("uploading")

      const formData = new FormData()
      formData.append("file", file)

      setState("processing")

      const apiUrl = process.env.NODE_ENV === 'development' 
        ? 'http://localhost:8000/api/extract'
        : '/api/extract'

      const response = await fetch(apiUrl, {
        method: "POST",
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || "Erreur lors de l'extraction")
      }

      const data = await response.json()
      
      if (data.requirements && data.requirements.length > 0) {
        setResult({
          filename: file.name,
          requirements: data.requirements,
          summary: data.summary
        })
        setState("success")
      } else {
        throw new Error("Aucune exigence PCI DSS trouvée dans le PDF")
      }
    } catch (error) {
      console.error("Extraction error:", error)
      setError(error instanceof Error ? error.message : "Erreur lors de l'extraction du PDF")
      setState("error")
      setTimeout(() => {
        setError(undefined)
        setState("idle")
      }, 5000)
    }
  }, [])

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      e.stopPropagation()
      setDragActive(false)

      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        handleFiles(e.dataTransfer.files)
      }
    },
    [handleFiles],
  )

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      e.preventDefault()
      if (e.target.files && e.target.files[0]) {
        handleFiles(e.target.files)
      }
    },
    [handleFiles],
  )

  const resetForm = () => {
    setState("idle")
    setResult(null)
    setError(undefined)
    if (fileInputRef.current) {
      fileInputRef.current.value = ""
    }
  }

  const downloadJson = () => {
    if (!result) return
    
    const blob = new Blob([JSON.stringify(result.requirements, null, 2)], {
      type: 'application/json',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    
    const now = new Date()
    const timestamp = now.toISOString().slice(0, 19).replace(/[:.]/g, '-')
    const fileName = `pci_requirements_${timestamp}.json`
    
    a.download = fileName
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  if (state === "success" && result) {
    return (
      <div className="flex flex-col gap-4 w-full">
        <div className="text-center space-y-2">
          <div className="text-lg font-medium text-slate-12">✅ Extraction réussie !</div>
          <div className="text-sm text-slate-10">{result.summary.total} exigences • {result.summary.total_tests} tests</div>
        </div>

        <div className="grid grid-cols-2 gap-3 p-4 bg-slate-2 rounded-lg">
          <div className="text-center">
            <div className="text-lg font-semibold text-slate-12">{result.summary.total}</div>
            <div className="text-xs text-slate-10">Exigences</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-slate-12">{result.summary.total_tests}</div>
            <div className="text-xs text-slate-10">Tests</div>
          </div>
        </div>

        <div className="flex gap-2">
          <button
            onClick={downloadJson}
            className="flex-1 bg-slate-12 text-slate-1 text-sm font-medium py-2 px-4 rounded-full text-center hover:bg-slate-11 transition-colors flex items-center justify-center gap-2"
          >
            <Download className="w-4 h-4" />
            Télécharger JSON
          </button>
          <button
            onClick={resetForm}
            className="bg-slate-3 text-slate-11 text-sm font-medium py-2 px-4 rounded-full hover:bg-slate-4 transition-colors flex items-center justify-center gap-2"
          >
            <X className="w-4 h-4" />
            Nouveau
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4 w-full">
      <div
        className={clsx(
          "relative border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200",
          dragActive ? "border-slate-8 bg-slate-2" : "border-slate-6 bg-slate-1",
          state === "idle" ? "hover:border-slate-8 hover:bg-slate-2" : "",
          state === "uploading" || state === "processing" ? "opacity-50 pointer-events-none" : "",
        )}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          onChange={handleInputChange}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          disabled={state === "uploading" || state === "processing"}
        />

        <div className="space-y-4">
          <div className="flex justify-center">
            {state === "uploading" || state === "processing" ? (
              <div className="w-12 h-12 rounded-full border-2 border-slate-6 border-t-slate-12 animate-spin" />
            ) : (
              <div className="w-12 h-12 rounded-full bg-slate-3 flex items-center justify-center">
                <Upload className="w-6 h-6 text-slate-11" />
              </div>
            )}
          </div>

          <div className="space-y-2">
            <div className="text-sm font-medium text-slate-12">
              {state === "uploading" && "Téléchargement..."}
              {state === "processing" && "Extraction en cours..."}
              {state === "idle" && "Glissez votre PDF PCI DSS ici"}
            </div>
            <div className="text-xs text-slate-10">
              {state === "idle" && "ou cliquez pour sélectionner un fichier"}
              {state === "uploading" && "Veuillez patienter..."}
              {state === "processing" && "Analyse des exigences en cours..."}
            </div>
          </div>

          {state === "idle" && (
            <div className="flex items-center justify-center gap-2 text-xs text-slate-9">
              <FileText className="w-4 h-4" />
              PDF uniquement • Max 50MB
            </div>
          )}
        </div>
      </div>

      {error && (
        <div className="text-xs text-red-500 text-center bg-red-50 dark:bg-red-950/20 p-2 rounded-lg">{error}</div>
      )}
    </div>
  )
}