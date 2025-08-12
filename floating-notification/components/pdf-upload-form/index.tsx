"use client"
import clsx from "clsx"
import type React from "react"

import { useRef, useState, useCallback } from "react"
import { Upload, FileText, Download, X } from "lucide-react"

type ConversionResult = {
  filename: string
  images: string[]
  downloadUrl: string
}

type State = "idle" | "uploading" | "converting" | "success" | "error"

export function PdfUploadForm() {
  const [state, setState] = useState<State>("idle")
  const [error, setError] = useState<string>()
  const [result, setResult] = useState<ConversionResult | null>(null)
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

    if (file.size > 10 * 1024 * 1024) {
      // 10MB limit
      setError("Le fichier est trop volumineux (max 10MB)")
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
      formData.append("pdf", file)

      setState("converting")

      const response = await fetch("/api/convert-pdf", {
        method: "POST",
        body: formData,
      })

      if (!response.ok) {
        throw new Error("Erreur lors de la conversion")
      }

      const result = await response.json()
      setResult(result)
      setState("success")
    } catch (error) {
      console.error("Conversion error:", error)
      setError("Erreur lors de la conversion du PDF")
      setState("error")
      setTimeout(() => {
        setError(undefined)
        setState("idle")
      }, 3000)
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

  if (state === "success" && result) {
    return (
      <div className="flex flex-col gap-4 w-full">
        <div className="text-center space-y-2">
          <div className="text-lg font-medium text-slate-12">✅ Conversion réussie !</div>
          <div className="text-sm text-slate-10">{result.images.length} image(s) générée(s)</div>
        </div>

        <div className="grid grid-cols-2 gap-2 max-h-40 overflow-y-auto">
          {result.images.map((image, index) => (
            <div key={index} className="relative">
              <img
                src={image || "/placeholder.svg"}
                alt={`Page ${index + 1}`}
                className="w-full h-20 object-cover rounded-lg border border-slate-6"
              />
              <div className="absolute bottom-1 left-1 bg-slate-12 text-slate-1 text-xs px-1 rounded">{index + 1}</div>
            </div>
          ))}
        </div>

        <div className="flex gap-2">
          <a
            href={result.downloadUrl}
            download
            className="flex-1 bg-slate-12 text-slate-1 text-sm font-medium py-2 px-4 rounded-full text-center hover:bg-slate-11 transition-colors flex items-center justify-center gap-2"
          >
            <Download className="w-4 h-4" />
            Télécharger tout
          </a>
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
          state === "uploading" || state === "converting" ? "opacity-50 pointer-events-none" : "",
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
          disabled={state === "uploading" || state === "converting"}
        />

        <div className="space-y-4">
          <div className="flex justify-center">
            {state === "uploading" || state === "converting" ? (
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
              {state === "converting" && "Conversion en cours..."}
              {state === "idle" && "Glissez votre PDF ici"}
            </div>
            <div className="text-xs text-slate-10">
              {state === "idle" && "ou cliquez pour sélectionner un fichier"}
              {state === "uploading" && "Veuillez patienter..."}
              {state === "converting" && "Transformation de votre PDF en images..."}
            </div>
          </div>

          {state === "idle" && (
            <div className="flex items-center justify-center gap-2 text-xs text-slate-9">
              <FileText className="w-4 h-4" />
              PDF uniquement • Max 10MB
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
