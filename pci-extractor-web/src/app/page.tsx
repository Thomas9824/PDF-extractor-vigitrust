'use client'

import { useState } from 'react'

export default function Home() {
  const [file, setFile] = useState<File | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  const [extractedData, setExtractedData] = useState<Array<{req_num: string, text: string, tests: string[], guidance: string}> | null>(null)
  const [languageInfo, setLanguageInfo] = useState<any>(null)

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const uploadedFile = event.target.files?.[0]
    if (uploadedFile && uploadedFile.type === 'application/pdf') {
      setFile(uploadedFile)
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    
    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile && droppedFile.type === 'application/pdf') {
      setFile(droppedFile)
    }
  }

  const processFile = async () => {
    if (!file) {
      console.error('No file selected')
      return
    }

    console.log('Starting PDF processing...', file.name)
    setIsProcessing(true)
    
    try {
      const formData = new FormData()
      formData.append('file', file)
      console.log('FormData created, sending request...')

      // En développement local, utiliser l'API Python directe
      // En production, utiliser l'URL relative qui sera routée par Vercel
      const apiUrl = process.env.NODE_ENV === 'development' 
        ? 'http://localhost:8000/api/extract'
        : '/api/extract'
      
      const response = await fetch(apiUrl, {
        method: 'POST',
        body: formData,
      })

      console.log('Response received:', response.status, response.statusText)
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(`Server error: ${errorData.error || response.statusText}`)
      }

      const data = await response.json()
      console.log('Data received:', data)
      
      if (data.requirements && data.requirements.length > 0) {
        console.log(`Found ${data.requirements.length} requirements`)
        setExtractedData(data.requirements)
        
        // Capturer les informations de langue si disponibles
        if (data.summary && data.summary.language_detection) {
          setLanguageInfo(data.summary.language_detection)
          console.log('Language detected:', data.summary.language_detection)
        }
      } else {
        console.warn('No requirements found in response')
      }
    } catch (error) {
      console.error('Error processing file:', error)
    } finally {
      setIsProcessing(false)
    }
  }

  const downloadJSON = () => {
    if (!extractedData) return
    
    const blob = new Blob([JSON.stringify(extractedData, null, 2)], {
      type: 'application/json',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    
    const now = new Date()
    const timestamp = now.toISOString().slice(0, 19).replace(/[:.]/g, '-')
    const languageSuffix = languageInfo?.code ? `_${languageInfo.code}` : ''
    const fileName = `pci_requirements${languageSuffix}_${timestamp}.json`
    
    a.download = fileName
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const downloadCSV = () => {
    if (!extractedData) return
    
    const headers = ['reqid', 'pci_requirement_fr', 'tp', 'guidance']
    const csvContent = [
      headers.join(','),
      ...extractedData.map((item) => [
        `"${(item.req_num || '').replace(/"/g, '""')}"`,
        `"${(item.text || '').replace(/"/g, '""')}"`,
        `"${(Array.isArray(item.tests) ? item.tests.join('; ') : item.tests || '').replace(/"/g, '""')}"`,
        `"${(item.guidance || '').replace(/"/g, '""')}"`
      ].join(','))
    ].join('\n')
    
    const blob = new Blob([csvContent], {
      type: 'text/csv;charset=utf-8;',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    
    const now = new Date()
    const timestamp = now.toISOString().slice(0, 19).replace(/[:.]/g, '-')
    const languageSuffix = languageInfo?.code ? `_${languageInfo.code}` : ''
    const fileName = `pci_requirements${languageSuffix}_${timestamp}.csv`
    
    a.download = fileName
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="min-h-screen bg-black flex items-center justify-center relative overflow-hidden">
      {/* Gradient Background Effects */}
      <div className="absolute inset-0 bg-gradient-to-br from-red-500/10 via-black to-red-500/10"></div>
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-gradient-to-r from-red-500/20 to-red-600/20 rounded-full blur-3xl animate-pulse"></div>
      <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-gradient-to-l from-red-600/15 to-red-500/15 rounded-full blur-3xl animate-pulse delay-1000"></div>
      
      {/* Main Container */}
      <div className="relative z-10 w-full max-w-md mx-auto px-6">
        
        {/* Header */}
        <div className="text-center mb-12">
          <div className="mb-6">
            <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-r from-red-500 to-red-600 rounded-2xl flex items-center justify-center">
              <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
          </div>
          <h1 className="text-3xl font-light text-white mb-2 tracking-tight">
            PCI DSS Extractor
          </h1>
          <p className="text-gray-400 text-sm font-light">
            Extract requirements from your PDF document
          </p>
        </div>

        {/* Upload Area */}
        <div 
          className={`relative mb-8 transition-all duration-300 ${
            isDragging ? 'scale-105' : 'scale-100'
          }`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileUpload}
            className="hidden"
            id="file-upload"
          />
          
          <label
            htmlFor="file-upload"
            className={`relative block w-full p-8 border-2 border-dashed rounded-2xl cursor-pointer transition-all duration-300 group ${
              isDragging 
                ? 'border-red-500/50 bg-red-500/5' 
                : file 
                ? 'border-red-500/30 bg-red-500/5' 
                : 'border-gray-700 hover:border-gray-600 hover:bg-gray-900/20'
            }`}
          >
            <div className="text-center">
              <div className={`mx-auto w-12 h-12 mb-4 rounded-full flex items-center justify-center transition-all duration-300 ${
                file 
                  ? 'bg-gradient-to-r from-red-500 to-red-600' 
                  : 'bg-gray-800 group-hover:bg-gray-700'
              }`}>
                {file ? (
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  <svg className="w-6 h-6 text-gray-400 group-hover:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                )}
              </div>
              
              {file ? (
                <div>
                  <p className="text-white font-medium mb-1">{file.name}</p>
                  <p className="text-gray-400 text-sm">Click to change file</p>
                </div>
              ) : (
                <div>
                  <p className="text-white mb-1">Drop your PDF here</p>
                  <p className="text-gray-400 text-sm">or click to browse</p>
                </div>
              )}
            </div>
          </label>
        </div>

        {/* Process Button */}
        {file && !extractedData && (
          <button
            onClick={processFile}
            disabled={isProcessing}
            className={`w-full py-4 px-6 rounded-2xl font-medium text-white transition-all duration-300 ${
              isProcessing
                ? 'bg-gray-700 cursor-not-allowed'
                : 'bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 transform hover:scale-[1.02] active:scale-[0.98]'
            }`}
          >
            {isProcessing ? (
              <div className="flex items-center justify-center">
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin mr-3"></div>
                Processing...
              </div>
            ) : (
              'Extract Requirements'
            )}
          </button>
        )}

        {/* Language Detection Info */}
        {languageInfo && (
          <div className="mb-6 p-4 rounded-2xl bg-gray-900/50 border border-gray-700">
            <div className="flex items-center mb-2">
              <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
              <h3 className="text-white font-medium">Language Detection</h3>
            </div>
            <div className="space-y-1 text-sm">
              <p className="text-gray-300">
                <span className="text-gray-400">Detected:</span> {languageInfo.name_en || languageInfo.name}
              </p>
              <p className="text-gray-300">
                <span className="text-gray-400">Confidence:</span> {languageInfo.confidence_percentage}
              </p>
              <p className="text-gray-300">
                <span className="text-gray-400">Extractor:</span> {languageInfo.extractor}
              </p>
            </div>
          </div>
        )}

        {/* Download Buttons */}
        {extractedData && (
          <div className="space-y-3">
            <button
              onClick={downloadJSON}
              className="w-full py-4 px-6 rounded-2xl font-medium text-white bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 transform hover:scale-[1.02] active:scale-[0.98] transition-all duration-300"
            >
              Download as JSON
            </button>
            <button
              onClick={downloadCSV}
              className="w-full py-4 px-6 rounded-2xl font-medium text-white bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 transform hover:scale-[1.02] active:scale-[0.98] transition-all duration-300"
            >
              Download as CSV
            </button>
          </div>
        )}

      </div>
    </div>
  )
}