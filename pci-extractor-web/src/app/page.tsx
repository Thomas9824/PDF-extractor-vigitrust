'use client'

import { useState } from 'react'

export default function Home() {
  const [file, setFile] = useState<File | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [isDragging, setIsDragging] = useState(false)

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
        
        // Télécharger automatiquement le JSON
        const blob = new Blob([JSON.stringify(data.requirements, null, 2)], {
          type: 'application/json',
        })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        
        // Générer le nom de fichier avec la date
        const now = new Date()
        const timestamp = now.toISOString().slice(0, 19).replace(/[:.]/g, '-')
        const fileName = `pci_requirements_${timestamp}.json`
        
        a.download = fileName
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
        
        console.log(`JSON downloaded as: ${fileName}`)
      } else {
        console.warn('No requirements found in response')
      }
    } catch (error) {
      console.error('Error processing file:', error)
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div className="min-h-screen bg-black flex items-center justify-center relative overflow-hidden">
      {/* Gradient Background Effects */}
      <div className="absolute inset-0 bg-gradient-to-br from-orange-500/10 via-black to-pink-500/10"></div>
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-gradient-to-r from-orange-500/20 to-pink-500/20 rounded-full blur-3xl animate-pulse"></div>
      <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-gradient-to-l from-pink-500/15 to-orange-500/15 rounded-full blur-3xl animate-pulse delay-1000"></div>
      
      {/* Main Container */}
      <div className="relative z-10 w-full max-w-md mx-auto px-6">
        
        {/* Header */}
        <div className="text-center mb-12">
          <div className="mb-6">
            <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-r from-orange-500 to-pink-500 rounded-2xl flex items-center justify-center">
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
                ? 'border-orange-500/50 bg-orange-500/5' 
                : file 
                ? 'border-pink-500/30 bg-pink-500/5' 
                : 'border-gray-700 hover:border-gray-600 hover:bg-gray-900/20'
            }`}
          >
            <div className="text-center">
              <div className={`mx-auto w-12 h-12 mb-4 rounded-full flex items-center justify-center transition-all duration-300 ${
                file 
                  ? 'bg-gradient-to-r from-orange-500 to-pink-500' 
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
        {file && (
          <button
            onClick={processFile}
            disabled={isProcessing}
            className={`w-full py-4 px-6 rounded-2xl font-medium text-white transition-all duration-300 ${
              isProcessing
                ? 'bg-gray-700 cursor-not-allowed'
                : 'bg-gradient-to-r from-orange-500 to-pink-500 hover:from-orange-600 hover:to-pink-600 transform hover:scale-[1.02] active:scale-[0.98]'
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

        {/* Success/Error Messages */}
        <div className="mt-8 text-center">
          <p className="text-gray-500 text-xs">
            Secure • Fast • Automated
          </p>
        </div>
      </div>
    </div>
  )
}