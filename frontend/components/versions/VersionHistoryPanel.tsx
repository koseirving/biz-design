'use client'

import React, { useState, useEffect } from 'react'
import { format } from 'date-fns'

interface Version {
  id: string
  version_number: number
  content: any
  created_at: string
  created_by: string
  is_auto_save: boolean
  is_current: boolean
  change_summary?: string
}

interface VersionHistoryPanelProps {
  outputId: string
  currentVersionId?: string
  onRestore?: (versionId: string) => void
  onPreview?: (version: Version) => void
  onCompare?: (version1: Version, version2: Version) => void
}

export default function VersionHistoryPanel({
  outputId,
  currentVersionId,
  onRestore,
  onPreview,
  onCompare
}: VersionHistoryPanelProps) {
  const [versions, setVersions] = useState<Version[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedVersions, setSelectedVersions] = useState<string[]>([])
  const [expandedVersion, setExpandedVersion] = useState<string | null>(null)

  useEffect(() => {
    fetchVersionHistory()
  }, [outputId])

  const fetchVersionHistory = async () => {
    try {
      setLoading(true)
      const response = await fetch(`/api/proxy/outputs/${outputId}/versions`, {
        method: 'GET',
        credentials: 'include'
      })
      
      if (!response.ok) {
        throw new Error('Failed to fetch version history')
      }
      
      const data = await response.json()
      setVersions(data.versions || [])
    } catch (error) {
      console.error('Error fetching version history:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleRestore = async (versionId: string) => {
    try {
      const response = await fetch(`/api/proxy/outputs/${outputId}/versions/${versionId}/restore`, {
        method: 'POST',
        credentials: 'include'
      })
      
      if (!response.ok) {
        throw new Error('Failed to restore version')
      }
      
      await fetchVersionHistory()
      onRestore?.(versionId)
    } catch (error) {
      console.error('Error restoring version:', error)
    }
  }

  const handleVersionSelect = (versionId: string) => {
    setSelectedVersions(prev => {
      if (prev.includes(versionId)) {
        return prev.filter(id => id !== versionId)
      }
      if (prev.length >= 2) {
        return [prev[1], versionId]
      }
      return [...prev, versionId]
    })
  }

  const handleCompare = () => {
    if (selectedVersions.length === 2) {
      const version1 = versions.find(v => v.id === selectedVersions[0])
      const version2 = versions.find(v => v.id === selectedVersions[1])
      if (version1 && version2) {
        onCompare?.(version1, version2)
      }
    }
  }

  const toggleExpanded = (versionId: string) => {
    setExpandedVersion(expandedVersion === versionId ? null : versionId)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          Version History
        </h2>
        {selectedVersions.length === 2 && (
          <button
            onClick={handleCompare}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Compare Selected
          </button>
        )}
      </div>

      <div className="space-y-4">
        {versions.map((version) => (
          <div
            key={version.id}
            className={`border rounded-lg p-4 transition-all ${
              version.is_current
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                : 'border-gray-200 dark:border-gray-700'
            } ${
              selectedVersions.includes(version.id)
                ? 'ring-2 ring-blue-400'
                : ''
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-3">
                <input
                  type="checkbox"
                  checked={selectedVersions.includes(version.id)}
                  onChange={() => handleVersionSelect(version.id)}
                  className="mt-1 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  disabled={version.is_current}
                />
                
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <h3 className="font-semibold text-gray-900 dark:text-white">
                      Version {version.version_number}
                    </h3>
                    {version.is_current && (
                      <span className="px-2 py-1 text-xs bg-blue-500 text-white rounded-full">
                        Current
                      </span>
                    )}
                    {version.is_auto_save && (
                      <span className="px-2 py-1 text-xs bg-gray-500 text-white rounded-full">
                        Auto-save
                      </span>
                    )}
                  </div>
                  
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    {format(new Date(version.created_at), 'MMM dd, yyyy HH:mm')}
                  </p>
                  
                  {version.change_summary && (
                    <p className="text-sm text-gray-700 dark:text-gray-300 mt-2">
                      {version.change_summary}
                    </p>
                  )}
                  
                  <button
                    onClick={() => toggleExpanded(version.id)}
                    className="text-sm text-blue-600 hover:text-blue-700 mt-2"
                  >
                    {expandedVersion === version.id ? 'Hide Details' : 'Show Details'}
                  </button>
                  
                  {expandedVersion === version.id && (
                    <div className="mt-3 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
                      <pre className="text-xs text-gray-600 dark:text-gray-400 overflow-x-auto">
                        {JSON.stringify(version.content, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              </div>
              
              <div className="flex space-x-2">
                {onPreview && (
                  <button
                    onClick={() => onPreview(version)}
                    className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                  >
                    Preview
                  </button>
                )}
                
                {!version.is_current && (
                  <button
                    onClick={() => handleRestore(version.id)}
                    className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
                  >
                    Restore
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {versions.length === 0 && (
        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
          No version history available
        </div>
      )}
    </div>
  )
}