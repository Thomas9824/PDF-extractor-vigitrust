'use client'

import { useState, useRef, useCallback } from 'react'
import { Upload, FileText, Download, X, CheckCircle, AlertCircle } from 'lucide-react'
import clsx from 'clsx'

type State = "idle" | "uploading" | "processing" | "success" | "error"

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

export default function Home() {
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
      formData.append('file', file)

      setState("processing")

      const apiUrl = process.env.NODE_ENV === 'development' 
        ? 'http://localhost:8000/api/extract'
        : '/api/extract'
      
      const response = await fetch(apiUrl, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Erreur lors de l\'extraction')
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
        throw new Error('Aucune exigence PCI DSS trouvée dans le PDF')
      }
    } catch (error) {
      console.error('Extraction error:', error)
      setError(error instanceof Error ? error.message : 'Erreur lors de l\'extraction du PDF')
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

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex items-center justify-center p-4">
      <div className="w-full mx-auto max-w-[500px] flex flex-col justify-center items-center bg-white dark:bg-gray-900 pb-0 overflow-hidden rounded-2xl shadow-xl">
        
        {/* Header */}
        <div className="flex flex-col items-center gap-4 flex-1 text-center w-full p-8 pb-4">
          <div className="flex justify-center w-16 h-16 items-center mx-auto mb-4 bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl">
            <FileText className="w-8 h-8 text-white" />
          </div>

          <div className="space-y-1">
            <h1 className="text-2xl sm:text-3xl font-medium text-gray-900 dark:text-gray-100 whitespace-pre-wrap text-pretty">
              PCI DSS Extractor
            </h1>
            <div className="text-gray-600 dark:text-gray-400 text-sm tracking-tight text-pretty">
              <p>Extrayez automatiquement les exigences de vos documents PCI DSS en format JSON structuré</p>
            </div>
          </div>

          {/* Upload Form */}
          <div className="px-1 flex flex-col w-full self-stretch">
            {state === "success" && result ? (
              <div className="flex flex-col gap-4 w-full">
                <div className="text-center space-y-2">
                  <div className="flex items-center justify-center gap-2 text-lg font-medium text-green-600 dark:text-green-400">
                    <CheckCircle className="w-5 h-5" />
                    Extraction réussie !
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    {result.summary.total} exigences extraites • {result.summary.total_tests} tests identifiés
                  </div>
                </div>

                {/* Summary Stats */}
                <div className="grid grid-cols-2 gap-3 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <div className="text-center">
                    <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">{result.summary.total}</div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">Exigences</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">{result.summary.total_tests}</div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">Tests</div>
                  </div>
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={downloadJson}
                    className="flex-1 bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 text-sm font-medium py-3 px-4 rounded-full hover:bg-gray-800 dark:hover:bg-gray-200 transition-colors flex items-center justify-center gap-2"
                  >
                    <Download className="w-4 h-4" />
                    Télécharger JSON
                  </button>
                  <button
                    onClick={resetForm}
                    className="bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 text-sm font-medium py-3 px-4 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors flex items-center justify-center gap-2"
                  >
                    <X className="w-4 h-4" />
                    Nouveau
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex flex-col gap-4 w-full">
                <div
                  className={clsx(
                    "relative border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200",
                    dragActive 
                      ? "border-blue-400 bg-blue-50 dark:bg-blue-950/20" 
                      : "border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-800",
                    state === "idle" ? "hover:border-gray-400 dark:hover:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-750" : "",
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
                        <div className="w-12 h-12 rounded-full border-2 border-gray-300 border-t-gray-900 dark:border-gray-600 dark:border-t-gray-100 animate-spin" />
                      ) : (
                        <div className="w-12 h-12 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
                          <Upload className="w-6 h-6 text-gray-600 dark:text-gray-400" />
                        </div>
                      )}
                    </div>

                    <div className="space-y-2">
                      <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {state === "uploading" && "Téléchargement..."}
                        {state === "processing" && "Extraction en cours..."}
                        {state === "idle" && "Glissez votre PDF PCI DSS ici"}
                      </div>
                      <div className="text-xs text-gray-600 dark:text-gray-400">
                        {state === "idle" && "ou cliquez pour sélectionner un fichier"}
                        {state === "uploading" && "Veuillez patienter..."}
                        {state === "processing" && "Analyse des exigences en cours..."}
                      </div>
                    </div>

                    {state === "idle" && (
                      <div className="flex items-center justify-center gap-2 text-xs text-gray-500 dark:text-gray-500">
                        <FileText className="w-4 h-4" />
                        PDF uniquement • Max 50MB
                      </div>
                    )}
                  </div>
                </div>

                {error && (
                  <div className="flex items-center gap-2 text-xs text-red-600 dark:text-red-400 text-center bg-red-50 dark:bg-red-950/20 p-3 rounded-lg">
                    <AlertCircle className="w-4 h-4 flex-shrink-0" />
                    {error}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Features */}
          {state === "idle" && (
            <div className="grid grid-cols-1 gap-4 w-full text-center">
              <div className="space-y-2">
                <div className="text-sm font-medium text-gray-900 dark:text-gray-100">🔍 Extraction intelligente</div>
                <div className="text-xs text-gray-600 dark:text-gray-400">Détection automatique des exigences et tests</div>
              </div>
              <div className="space-y-2">
                <div className="text-sm font-medium text-gray-900 dark:text-gray-100">🔒 100% sécurisé</div>
                <div className="text-xs text-gray-600 dark:text-gray-400">Vos fichiers ne sont jamais stockés</div>
              </div>
              <div className="space-y-2">
                <div className="text-sm font-medium text-gray-900 dark:text-gray-100">📊 Format structuré</div>
                <div className="text-xs text-gray-600 dark:text-gray-400">JSON prêt à l&apos;emploi pour vos systèmes</div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <footer className="flex justify-between items-center w-full self-stretch px-8 py-3 text-sm bg-gray-100 dark:bg-gray-800 overflow-hidden">
          <p className="text-xs text-gray-600 dark:text-gray-400">© 2024 PCI DSS Extractor</p>
          <div className="text-xs text-gray-500 dark:text-gray-500">Powered by AI</div>
        </footer>
      </div>
    </div>
  )
}