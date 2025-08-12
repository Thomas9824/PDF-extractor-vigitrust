'use client'

import { useState } from 'react'

export default function Home() {
  const [file, setFile] = useState<File | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const uploadedFile = event.target.files?.[0]
    if (uploadedFile && uploadedFile.type === 'application/pdf') {
      setFile(uploadedFile)
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
        alert(`Extraction terminée! ${data.requirements.length} exigences extraites.\nFichier téléchargé: ${fileName}`)
      } else {
        console.warn('No requirements found in response')
        alert('Aucune exigence PCI DSS trouvée dans le PDF.')
      }
    } catch (error) {
      console.error('Error processing file:', error)
      alert(`Erreur lors du traitement du PDF: ${error instanceof Error ? error.message : 'Erreur inconnue'}`)
    } finally {
      setIsProcessing(false)
    }
  }


  return (
    <div className="min-h-screen bg-white p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            PCI DSS Requirements Extractor
          </h1>
          <p className="text-gray-600">
            Upload a PCI DSS PDF to extract requirements
          </p>
        </div>

        {/* File Upload */}
        <div className="bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-6 text-center mb-6">
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileUpload}
            className="hidden"
            id="file-upload"
          />
          <label
            htmlFor="file-upload"
            className="cursor-pointer inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            Select PDF File
          </label>
          {file && (
            <p className="mt-2 text-sm text-gray-600">
              Selected: {file.name}
            </p>
          )}
        </div>

        {/* Process Button */}
        {file && (
          <div className="text-center mb-6">
            <button
              onClick={processFile}
              disabled={isProcessing}
              className="px-6 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400"
            >
              {isProcessing ? 'Processing...' : 'Extract Requirements'}
            </button>
          </div>
        )}

        {/* Message d'information */}
        <div className="text-center text-gray-600 mt-8">
          <p className="text-lg mb-2">📄 Sélectionnez un fichier PDF PCI DSS</p>
          <p className="text-sm">L&apos;extraction générera automatiquement un fichier JSON téléchargeable</p>
        </div>
      </div>
    </div>
  )
}