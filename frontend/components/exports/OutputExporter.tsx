'use client'

import React, { useState, useRef } from 'react'
import jsPDF from 'jspdf'
import html2canvas from 'html2canvas'
import Papa from 'papaparse'

interface OutputData {
  id: string
  framework_name: string
  output_data: any
  created_at: string
  updated_at: string
  user_id: string
  version: number
}

interface ExportOptions {
  format: 'pdf' | 'png' | 'csv' | 'json'
  template?: 'business' | 'casual' | 'presentation'
  includeMetadata?: boolean
  pageOrientation?: 'portrait' | 'landscape'
  imageQuality?: number
}

interface OutputExporterProps {
  outputData: OutputData
  isOpen: boolean
  onClose: () => void
  onExportComplete?: (format: string, success: boolean) => void
}

export default function OutputExporter({
  outputData,
  isOpen,
  onClose,
  onExportComplete
}: OutputExporterProps) {
  const [exportOptions, setExportOptions] = useState<ExportOptions>({
    format: 'pdf',
    template: 'business',
    includeMetadata: true,
    pageOrientation: 'portrait',
    imageQuality: 0.95
  })
  const [isExporting, setIsExporting] = useState(false)
  const [exportStatus, setExportStatus] = useState<string>('')
  const previewRef = useRef<HTMLDivElement>(null)

  const handleExport = async () => {
    setIsExporting(true)
    setExportStatus('Preparing export...')
    
    try {
      switch (exportOptions.format) {
        case 'pdf':
          await exportToPDF()
          break
        case 'png':
          await exportToPNG()
          break
        case 'csv':
          await exportToCSV()
          break
        case 'json':
          await exportToJSON()
          break
        default:
          throw new Error('Unsupported export format')
      }
      
      onExportComplete?.(exportOptions.format, true)
    } catch (error) {
      console.error('Export failed:', error)
      setExportStatus('Export failed')
      onExportComplete?.(exportOptions.format, false)
    } finally {
      setIsExporting(false)
      setTimeout(() => setExportStatus(''), 3000)
    }
  }

  const exportToPDF = async () => {
    setExportStatus('Generating PDF...')
    
    if (!previewRef.current) {
      throw new Error('Preview element not found')
    }

    // Create canvas from HTML element
    const canvas = await html2canvas(previewRef.current, {
      scale: 2,
      useCORS: true,
      allowTaint: true
    })

    const imgData = canvas.toDataURL('image/png')
    
    // Create PDF
    const pdf = new jsPDF({
      orientation: exportOptions.pageOrientation,
      unit: 'mm',
      format: 'a4'
    })

    const pdfWidth = pdf.internal.pageSize.getWidth()
    const pdfHeight = pdf.internal.pageSize.getHeight()
    
    const imgWidth = pdfWidth - 20 // 10mm margin on each side
    const imgHeight = (canvas.height * imgWidth) / canvas.width
    
    let heightLeft = imgHeight
    let position = 10 // 10mm top margin

    // Add first page
    pdf.addImage(imgData, 'PNG', 10, position, imgWidth, imgHeight)
    heightLeft -= (pdfHeight - 20)

    // Add additional pages if needed
    while (heightLeft >= 0) {
      position = heightLeft - imgHeight + 10
      pdf.addPage()
      pdf.addImage(imgData, 'PNG', 10, position, imgWidth, imgHeight)
      heightLeft -= (pdfHeight - 20)
    }

    // Add metadata if requested
    if (exportOptions.includeMetadata) {
      pdf.addPage()
      pdf.setFontSize(16)
      pdf.text('Export Metadata', 10, 20)
      pdf.setFontSize(12)
      pdf.text(`Framework: ${outputData.framework_name}`, 10, 35)
      pdf.text(`Created: ${new Date(outputData.created_at).toLocaleString()}`, 10, 45)
      pdf.text(`Updated: ${new Date(outputData.updated_at).toLocaleString()}`, 10, 55)
      pdf.text(`Version: ${outputData.version}`, 10, 65)
      pdf.text(`Export Date: ${new Date().toLocaleString()}`, 10, 75)
    }

    const fileName = `${outputData.framework_name.replace(/\s+/g, '_').toLowerCase()}_${new Date().getTime()}.pdf`
    pdf.save(fileName)
    
    setExportStatus('PDF downloaded successfully!')
  }

  const exportToPNG = async () => {
    setExportStatus('Generating PNG...')
    
    if (!previewRef.current) {
      throw new Error('Preview element not found')
    }

    const canvas = await html2canvas(previewRef.current, {
      scale: 2,
      useCORS: true,
      allowTaint: true
    })

    // Convert to blob and download
    canvas.toBlob((blob) => {
      if (!blob) {
        throw new Error('Failed to create image')
      }
      
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${outputData.framework_name.replace(/\s+/g, '_').toLowerCase()}_${new Date().getTime()}.png`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      
      setExportStatus('PNG downloaded successfully!')
    }, 'image/png', exportOptions.imageQuality)
  }

  const exportToCSV = async () => {
    setExportStatus('Generating CSV...')
    
    // Convert output data to flat structure for CSV
    const flattenData = (obj: any, prefix = ''): any => {
      const flattened: any = {}
      
      for (const [key, value] of Object.entries(obj)) {
        const newKey = prefix ? `${prefix}.${key}` : key
        
        if (value && typeof value === 'object' && !Array.isArray(value)) {
          Object.assign(flattened, flattenData(value, newKey))
        } else if (Array.isArray(value)) {
          flattened[newKey] = value.join('; ')
        } else {
          flattened[newKey] = value
        }
      }
      
      return flattened
    }

    const csvData = [
      {
        framework: outputData.framework_name,
        created_at: outputData.created_at,
        updated_at: outputData.updated_at,
        version: outputData.version,
        ...flattenData(outputData.output_data)
      }
    ]

    if (exportOptions.includeMetadata) {
      csvData.push({
        framework: 'METADATA',
        created_at: 'Export Date',
        updated_at: new Date().toISOString(),
        version: 'Export Version',
        ...Object.keys(flattenData(outputData.output_data)).reduce((acc, key) => {
          acc[key] = 'Generated by Biz Design Platform'
          return acc
        }, {} as any)
      })
    }

    const csv = Papa.unparse(csvData)
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    
    const link = document.createElement('a')
    link.href = url
    link.download = `${outputData.framework_name.replace(/\s+/g, '_').toLowerCase()}_${new Date().getTime()}.csv`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    
    setExportStatus('CSV downloaded successfully!')
  }

  const exportToJSON = async () => {
    setExportStatus('Generating JSON...')
    
    const jsonData = {
      ...(exportOptions.includeMetadata && {
        metadata: {
          export_date: new Date().toISOString(),
          export_version: '1.0',
          platform: 'Biz Design Platform'
        }
      }),
      framework_name: outputData.framework_name,
      created_at: outputData.created_at,
      updated_at: outputData.updated_at,
      version: outputData.version,
      output_data: outputData.output_data
    }

    const jsonString = JSON.stringify(jsonData, null, 2)
    const blob = new Blob([jsonString], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    
    const link = document.createElement('a')
    link.href = url
    link.download = `${outputData.framework_name.replace(/\s+/g, '_').toLowerCase()}_${new Date().getTime()}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    
    setExportStatus('JSON downloaded successfully!')
  }

  const renderPreview = () => {
    const { output_data } = outputData
    
    return (
      <div 
        ref={previewRef}
        className={`bg-white p-8 rounded-lg ${getTemplateStyles()}`}
        style={{ minHeight: '600px', width: '100%' }}
      >
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            {outputData.framework_name}
          </h1>
          <p className="text-gray-600">
            Generated on {new Date().toLocaleDateString()}
          </p>
        </div>

        {/* Content based on framework type */}
        {outputData.framework_name.toLowerCase().includes('swot') && renderSWOTPreview(output_data)}
        {outputData.framework_name.toLowerCase().includes('journey') && renderJourneyPreview(output_data)}
        {outputData.framework_name.toLowerCase().includes('canvas') && renderCanvasPreview(output_data)}
        
        {/* Generic fallback */}
        {!outputData.framework_name.toLowerCase().includes('swot') && 
         !outputData.framework_name.toLowerCase().includes('journey') && 
         !outputData.framework_name.toLowerCase().includes('canvas') && (
          <div className="space-y-4">
            {Object.entries(output_data || {}).map(([key, value]) => (
              <div key={key} className="border-b border-gray-200 pb-4">
                <h3 className="font-semibold text-gray-900 capitalize mb-2">
                  {key.replace(/_/g, ' ')}
                </h3>
                <div className="text-gray-700">
                  {Array.isArray(value) ? (
                    <ul className="list-disc list-inside space-y-1">
                      {value.map((item, index) => (
                        <li key={index}>{typeof item === 'string' ? item : JSON.stringify(item)}</li>
                      ))}
                    </ul>
                  ) : typeof value === 'object' ? (
                    <pre className="bg-gray-100 p-3 rounded text-sm">
                      {JSON.stringify(value, null, 2)}
                    </pre>
                  ) : (
                    <p>{String(value)}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Metadata footer */}
        {exportOptions.includeMetadata && (
          <div className="mt-8 pt-4 border-t border-gray-200 text-sm text-gray-500">
            <div className="grid grid-cols-2 gap-4">
              <div>Version: {outputData.version}</div>
              <div>Created: {new Date(outputData.created_at).toLocaleDateString()}</div>
            </div>
          </div>
        )}
      </div>
    )
  }

  const renderSWOTPreview = (data: any) => (
    <div className="grid grid-cols-2 gap-6">
      <div className="bg-green-50 p-4 rounded-lg">
        <h3 className="font-bold text-green-800 mb-3">Strengths</h3>
        <ul className="space-y-2 text-green-700">
          {(data.strengths || []).map((item: string, index: number) => (
            <li key={index} className="flex items-start">
              <span className="text-green-500 mr-2">•</span>
              {item}
            </li>
          ))}
        </ul>
      </div>
      <div className="bg-red-50 p-4 rounded-lg">
        <h3 className="font-bold text-red-800 mb-3">Weaknesses</h3>
        <ul className="space-y-2 text-red-700">
          {(data.weaknesses || []).map((item: string, index: number) => (
            <li key={index} className="flex items-start">
              <span className="text-red-500 mr-2">•</span>
              {item}
            </li>
          ))}
        </ul>
      </div>
      <div className="bg-blue-50 p-4 rounded-lg">
        <h3 className="font-bold text-blue-800 mb-3">Opportunities</h3>
        <ul className="space-y-2 text-blue-700">
          {(data.opportunities || []).map((item: string, index: number) => (
            <li key={index} className="flex items-start">
              <span className="text-blue-500 mr-2">•</span>
              {item}
            </li>
          ))}
        </ul>
      </div>
      <div className="bg-yellow-50 p-4 rounded-lg">
        <h3 className="font-bold text-yellow-800 mb-3">Threats</h3>
        <ul className="space-y-2 text-yellow-700">
          {(data.threats || []).map((item: string, index: number) => (
            <li key={index} className="flex items-start">
              <span className="text-yellow-500 mr-2">•</span>
              {item}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )

  const renderJourneyPreview = (data: any) => (
    <div className="space-y-6">
      {(data.stages || []).map((stage: any, index: number) => (
        <div key={index} className="border border-gray-200 rounded-lg p-4">
          <h3 className="font-bold text-gray-900 mb-2">{stage.name || `Stage ${index + 1}`}</h3>
          <p className="text-gray-700 mb-3">{stage.description}</p>
          {stage.touchpoints && (
            <div>
              <h4 className="font-medium text-gray-800 mb-2">Touchpoints:</h4>
              <ul className="list-disc list-inside text-gray-600">
                {stage.touchpoints.map((touchpoint: string, tIndex: number) => (
                  <li key={tIndex}>{touchpoint}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ))}
    </div>
  )

  const renderCanvasPreview = (data: any) => (
    <div className="grid grid-cols-3 gap-4">
      {Object.entries(data || {}).map(([key, value]) => (
        <div key={key} className="border border-gray-200 rounded-lg p-4">
          <h3 className="font-bold text-gray-900 mb-2 capitalize">
            {key.replace(/_/g, ' ')}
          </h3>
          <div className="text-gray-700 text-sm">
            {Array.isArray(value) ? (
              <ul className="space-y-1">
                {value.map((item, index) => (
                  <li key={index}>• {String(item)}</li>
                ))}
              </ul>
            ) : (
              <p>{String(value)}</p>
            )}
          </div>
        </div>
      ))}
    </div>
  )

  const getTemplateStyles = () => {
    switch (exportOptions.template) {
      case 'business':
        return 'font-serif border-2 border-gray-300'
      case 'casual':
        return 'font-sans bg-gradient-to-br from-blue-50 to-purple-50'
      case 'presentation':
        return 'font-sans bg-gray-50 border border-gray-200'
      default:
        return 'font-sans'
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden flex">
        {/* Settings Panel */}
        <div className="w-1/3 p-6 border-r border-gray-200 dark:border-gray-700">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">Export Settings</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
            >
              ✕
            </button>
          </div>

          <div className="space-y-6">
            {/* Format Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Export Format
              </label>
              <select
                value={exportOptions.format}
                onChange={(e) => setExportOptions(prev => ({ ...prev, format: e.target.value as any }))}
                className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
              >
                <option value="pdf">PDF Document</option>
                <option value="png">PNG Image</option>
                <option value="csv">CSV Data</option>
                <option value="json">JSON Data</option>
              </select>
            </div>

            {/* Template Selection (PDF/PNG only) */}
            {(exportOptions.format === 'pdf' || exportOptions.format === 'png') && (
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Template Style
                </label>
                <select
                  value={exportOptions.template}
                  onChange={(e) => setExportOptions(prev => ({ ...prev, template: e.target.value as any }))}
                  className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
                >
                  <option value="business">Business Formal</option>
                  <option value="casual">Casual</option>
                  <option value="presentation">Presentation</option>
                </select>
              </div>
            )}

            {/* Page Orientation (PDF only) */}
            {exportOptions.format === 'pdf' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Page Orientation
                </label>
                <div className="flex space-x-4">
                  <label className="flex items-center">
                    <input
                      type="radio"
                      value="portrait"
                      checked={exportOptions.pageOrientation === 'portrait'}
                      onChange={(e) => setExportOptions(prev => ({ ...prev, pageOrientation: e.target.value as any }))}
                      className="mr-2"
                    />
                    Portrait
                  </label>
                  <label className="flex items-center">
                    <input
                      type="radio"
                      value="landscape"
                      checked={exportOptions.pageOrientation === 'landscape'}
                      onChange={(e) => setExportOptions(prev => ({ ...prev, pageOrientation: e.target.value as any }))}
                      className="mr-2"
                    />
                    Landscape
                  </label>
                </div>
              </div>
            )}

            {/* Include Metadata */}
            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={exportOptions.includeMetadata}
                  onChange={(e) => setExportOptions(prev => ({ ...prev, includeMetadata: e.target.checked }))}
                  className="mr-2"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">Include metadata</span>
              </label>
            </div>

            {/* Image Quality (PNG only) */}
            {exportOptions.format === 'png' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Image Quality: {Math.round(exportOptions.imageQuality! * 100)}%
                </label>
                <input
                  type="range"
                  min="0.1"
                  max="1"
                  step="0.05"
                  value={exportOptions.imageQuality}
                  onChange={(e) => setExportOptions(prev => ({ ...prev, imageQuality: parseFloat(e.target.value) }))}
                  className="w-full"
                />
              </div>
            )}
          </div>

          {/* Export Button */}
          <button
            onClick={handleExport}
            disabled={isExporting}
            className="w-full mt-8 bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isExporting ? 'Exporting...' : `Export as ${exportOptions.format.toUpperCase()}`}
          </button>

          {exportStatus && (
            <p className={`mt-3 text-sm ${exportStatus.includes('success') ? 'text-green-600' : exportStatus.includes('failed') ? 'text-red-600' : 'text-blue-600'}`}>
              {exportStatus}
            </p>
          )}
        </div>

        {/* Preview Panel */}
        <div className="flex-1 p-6 overflow-auto bg-gray-100 dark:bg-gray-900">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Preview</h3>
          <div className="bg-white rounded-lg shadow-sm">
            {renderPreview()}
          </div>
        </div>
      </div>
    </div>
  )
}