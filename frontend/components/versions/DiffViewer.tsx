'use client'

import React, { useState, useEffect } from 'react'
import * as Diff from 'diff'

interface DiffViewerProps {
  version1Id: string
  version2Id: string
  outputId: string
  version1Label?: string
  version2Label?: string
  onClose?: () => void
}

interface DiffLine {
  type: 'added' | 'removed' | 'unchanged'
  content: string
  lineNumber: number
}

export default function DiffViewer({
  version1Id,
  version2Id,
  outputId,
  version1Label = 'Version A',
  version2Label = 'Version B',
  onClose
}: DiffViewerProps) {
  const [diffData, setDiffData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [viewMode, setViewMode] = useState<'unified' | 'split'>('unified')
  const [showOnlyChanges, setShowOnlyChanges] = useState(false)

  useEffect(() => {
    fetchDiff()
  }, [outputId, version1Id, version2Id])

  const fetchDiff = async () => {
    try {
      setLoading(true)
      const response = await fetch(
        `/api/proxy/outputs/${outputId}/versions/${version1Id}/diff/${version2Id}`,
        {
          method: 'GET',
          credentials: 'include'
        }
      )
      
      if (!response.ok) {
        throw new Error('Failed to fetch diff')
      }
      
      const data = await response.json()
      setDiffData(data)
    } catch (error) {
      console.error('Error fetching diff:', error)
    } finally {
      setLoading(false)
    }
  }

  const generateTextDiff = (text1: string, text2: string): DiffLine[] => {
    const diff = Diff.diffLines(text1, text2)
    const lines: DiffLine[] = []
    let lineNumber = 1

    diff.forEach((part) => {
      const partLines = part.value.split('\n').filter(line => line.length > 0 || part.value.endsWith('\n'))
      
      partLines.forEach((line, index) => {
        if (index === partLines.length - 1 && line === '' && !part.value.endsWith('\n')) {
          return // Skip empty last line if not intentional
        }
        
        lines.push({
          type: part.added ? 'added' : part.removed ? 'removed' : 'unchanged',
          content: line,
          lineNumber: lineNumber++
        })
      })
    })

    return lines
  }

  const renderFieldDiff = (field: string, oldValue: any, newValue: any) => {
    const oldText = typeof oldValue === 'string' ? oldValue : JSON.stringify(oldValue, null, 2)
    const newText = typeof newValue === 'string' ? newValue : JSON.stringify(newValue, null, 2)
    
    const diffLines = generateTextDiff(oldText, newText)
    const filteredLines = showOnlyChanges 
      ? diffLines.filter(line => line.type !== 'unchanged')
      : diffLines

    if (viewMode === 'split') {
      return (
        <div className="grid grid-cols-2 gap-4">
          <div>
            <h4 className="font-medium text-gray-900 dark:text-white mb-2">
              {version1Label}
            </h4>
            <pre className="text-sm bg-gray-50 dark:bg-gray-900 p-3 rounded overflow-x-auto">
              {oldText}
            </pre>
          </div>
          <div>
            <h4 className="font-medium text-gray-900 dark:text-white mb-2">
              {version2Label}
            </h4>
            <pre className="text-sm bg-gray-50 dark:bg-gray-900 p-3 rounded overflow-x-auto">
              {newText}
            </pre>
          </div>
        </div>
      )
    }

    return (
      <div className="space-y-1">
        {filteredLines.map((line, index) => (
          <div
            key={index}
            className={`text-sm font-mono p-2 rounded ${
              line.type === 'added'
                ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200'
                : line.type === 'removed'
                ? 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200'
                : 'bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300'
            }`}
          >
            <span className="inline-block w-8 text-gray-500 text-xs">
              {line.lineNumber}
            </span>
            <span className="inline-block w-4 text-center text-xs font-bold">
              {line.type === 'added' ? '+' : line.type === 'removed' ? '-' : ' '}
            </span>
            <span>{line.content}</span>
          </div>
        ))}
      </div>
    )
  }

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading diff...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg max-w-6xl max-h-[90vh] w-full flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              Version Comparison
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              {version1Label} vs {version2Label}
            </p>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <label className="text-sm text-gray-600 dark:text-gray-400">
                View:
              </label>
              <select
                value={viewMode}
                onChange={(e) => setViewMode(e.target.value as 'unified' | 'split')}
                className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded text-sm"
              >
                <option value="unified">Unified</option>
                <option value="split">Split</option>
              </select>
            </div>
            
            <label className="flex items-center space-x-2 text-sm">
              <input
                type="checkbox"
                checked={showOnlyChanges}
                onChange={(e) => setShowOnlyChanges(e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-gray-600 dark:text-gray-400">Only changes</span>
            </label>
            
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          {diffData && (
            <div className="space-y-6">
              {/* Summary */}
              <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                  Change Summary
                </h3>
                <div className="flex space-x-6 text-sm">
                  <span className="text-green-600">
                    +{diffData.summary?.additions || 0} additions
                  </span>
                  <span className="text-red-600">
                    -{diffData.summary?.deletions || 0} deletions
                  </span>
                  <span className="text-blue-600">
                    {diffData.summary?.modifications || 0} modifications
                  </span>
                </div>
              </div>

              {/* Field-by-field diff */}
              {diffData.changes && Object.entries(diffData.changes).map(([field, change]: [string, any]) => (
                <div key={field} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-3 capitalize">
                    {field.replace(/_/g, ' ')}
                  </h3>
                  
                  {change.type === 'modified' ? (
                    renderFieldDiff(field, change.old_value, change.new_value)
                  ) : change.type === 'added' ? (
                    <div className="bg-green-100 dark:bg-green-900/30 p-3 rounded">
                      <p className="text-green-800 dark:text-green-200 text-sm font-medium mb-2">
                        Field Added
                      </p>
                      <pre className="text-sm text-green-700 dark:text-green-300">
                        {typeof change.value === 'string' ? change.value : JSON.stringify(change.value, null, 2)}
                      </pre>
                    </div>
                  ) : change.type === 'removed' ? (
                    <div className="bg-red-100 dark:bg-red-900/30 p-3 rounded">
                      <p className="text-red-800 dark:text-red-200 text-sm font-medium mb-2">
                        Field Removed
                      </p>
                      <pre className="text-sm text-red-700 dark:text-red-300">
                        {typeof change.value === 'string' ? change.value : JSON.stringify(change.value, null, 2)}
                      </pre>
                    </div>
                  ) : (
                    <p className="text-gray-600 dark:text-gray-400 text-sm">No changes</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end space-x-3 p-6 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}