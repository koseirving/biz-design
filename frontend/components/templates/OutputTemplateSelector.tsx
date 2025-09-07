'use client'

import React, { useState, useEffect } from 'react'

interface Template {
  id: string
  name: string
  description: string
  preview: string
  category: 'business' | 'casual' | 'presentation' | 'modern'
  framework_types: string[]
  styles: TemplateStyles
}

interface TemplateStyles {
  backgroundColor: string
  primaryColor: string
  secondaryColor: string
  accentColor: string
  fontFamily: string
  headerStyle: string
  cardStyle: string
  spacing: string
  borderRadius: string
  shadows: boolean
  gridLayout: 'default' | '2x2' | '3x3' | 'linear' | 'masonry'
}

interface OutputTemplateSelectorProps {
  frameworkType: string
  currentTemplate?: string
  onSelectTemplate: (template: Template) => void
  onClose: () => void
  isOpen: boolean
  outputData?: any
}

const templates: Template[] = [
  {
    id: 'business-formal',
    name: 'Business Formal',
    description: 'Clean, professional design perfect for corporate presentations and reports',
    preview: '📊',
    category: 'business',
    framework_types: ['swot', 'canvas', 'journey', 'all'],
    styles: {
      backgroundColor: '#ffffff',
      primaryColor: '#1f2937',
      secondaryColor: '#6b7280',
      accentColor: '#3b82f6',
      fontFamily: 'font-serif',
      headerStyle: 'text-center border-b-2 border-gray-300 pb-4 mb-8',
      cardStyle: 'border border-gray-300 rounded-lg p-6 shadow-sm',
      spacing: 'space-y-6',
      borderRadius: 'rounded-lg',
      shadows: true,
      gridLayout: '2x2'
    }
  },
  {
    id: 'modern-minimal',
    name: 'Modern Minimal',
    description: 'Clean and minimal design with subtle gradients and modern typography',
    preview: '✨',
    category: 'modern',
    framework_types: ['swot', 'canvas', 'journey', 'all'],
    styles: {
      backgroundColor: '#f8fafc',
      primaryColor: '#0f172a',
      secondaryColor: '#64748b',
      accentColor: '#8b5cf6',
      fontFamily: 'font-sans',
      headerStyle: 'text-center pb-8 mb-8',
      cardStyle: 'bg-white border border-slate-200 rounded-2xl p-8 shadow-lg hover:shadow-xl transition-shadow',
      spacing: 'space-y-8',
      borderRadius: 'rounded-2xl',
      shadows: true,
      gridLayout: '2x2'
    }
  },
  {
    id: 'presentation-bold',
    name: 'Presentation Bold',
    description: 'High-contrast design optimized for presentations and large displays',
    preview: '🎯',
    category: 'presentation',
    framework_types: ['swot', 'canvas', 'journey', 'all'],
    styles: {
      backgroundColor: '#111827',
      primaryColor: '#ffffff',
      secondaryColor: '#d1d5db',
      accentColor: '#fbbf24',
      fontFamily: 'font-sans',
      headerStyle: 'text-center text-white pb-6 mb-8 border-b border-gray-600',
      cardStyle: 'bg-gray-800 border border-gray-600 rounded-xl p-6 text-white shadow-2xl',
      spacing: 'space-y-6',
      borderRadius: 'rounded-xl',
      shadows: true,
      gridLayout: '2x2'
    }
  },
  {
    id: 'casual-friendly',
    name: 'Casual & Friendly',
    description: 'Warm, approachable design with soft colors and rounded elements',
    preview: '🌈',
    category: 'casual',
    framework_types: ['swot', 'canvas', 'journey', 'all'],
    styles: {
      backgroundColor: 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)',
      primaryColor: '#92400e',
      secondaryColor: '#d97706',
      accentColor: '#f59e0b',
      fontFamily: 'font-sans',
      headerStyle: 'text-center pb-6 mb-8',
      cardStyle: 'bg-white/80 backdrop-blur-sm rounded-3xl p-6 shadow-lg border border-amber-200',
      spacing: 'space-y-6',
      borderRadius: 'rounded-3xl',
      shadows: true,
      gridLayout: '2x2'
    }
  },
  {
    id: 'tech-startup',
    name: 'Tech Startup',
    description: 'Modern tech-inspired design with gradients and sleek elements',
    preview: '🚀',
    category: 'modern',
    framework_types: ['canvas', 'swot', 'all'],
    styles: {
      backgroundColor: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      primaryColor: '#ffffff',
      secondaryColor: '#e5e7eb',
      accentColor: '#10b981',
      fontFamily: 'font-mono',
      headerStyle: 'text-center text-white pb-6 mb-8',
      cardStyle: 'bg-white/10 backdrop-blur-md rounded-2xl p-6 text-white border border-white/20 shadow-2xl',
      spacing: 'space-y-6',
      borderRadius: 'rounded-2xl',
      shadows: true,
      gridLayout: '2x2'
    }
  },
  {
    id: 'academic-paper',
    name: 'Academic Paper',
    description: 'Traditional academic format with clear hierarchy and readability',
    preview: '📚',
    category: 'business',
    framework_types: ['all'],
    styles: {
      backgroundColor: '#ffffff',
      primaryColor: '#1f2937',
      secondaryColor: '#4b5563',
      accentColor: '#dc2626',
      fontFamily: 'font-serif',
      headerStyle: 'text-center border-b-4 border-red-600 pb-4 mb-8',
      cardStyle: 'border-l-4 border-red-600 pl-6 py-4 bg-gray-50',
      spacing: 'space-y-8',
      borderRadius: 'rounded-none',
      shadows: false,
      gridLayout: 'linear'
    }
  }
]

export default function OutputTemplateSelector({
  frameworkType,
  currentTemplate,
  onSelectTemplate,
  onClose,
  isOpen,
  outputData
}: OutputTemplateSelectorProps) {
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null)
  const [previewData, setPreviewData] = useState<any>(null)
  const [filterCategory, setFilterCategory] = useState<string>('all')

  useEffect(() => {
    if (currentTemplate) {
      const template = templates.find(t => t.id === currentTemplate)
      setSelectedTemplate(template || null)
    }
  }, [currentTemplate])

  useEffect(() => {
    // Generate preview data based on framework type
    generatePreviewData()
  }, [frameworkType])

  const generatePreviewData = () => {
    const sampleData: any = {
      swot: {
        strengths: ['Strong brand recognition', 'Experienced team'],
        weaknesses: ['Limited resources', 'High costs'],
        opportunities: ['Market expansion', 'New partnerships'],
        threats: ['Competition', 'Regulatory changes']
      },
      canvas: {
        key_partners: ['Strategic partners', 'Suppliers'],
        key_activities: ['Product development', 'Marketing'],
        value_propositions: ['Unique solution', 'Cost-effective'],
        customer_relationships: ['Personal assistance', 'Self-service'],
        customer_segments: ['SMBs', 'Enterprise'],
        key_resources: ['Technology', 'Brand'],
        channels: ['Online', 'Retail'],
        cost_structure: ['Fixed costs', 'Variable costs'],
        revenue_streams: ['Subscriptions', 'One-time sales']
      },
      journey: {
        stages: [
          { name: 'Awareness', description: 'Customer discovers the product', touchpoints: ['Social media', 'Advertising'] },
          { name: 'Consideration', description: 'Customer evaluates options', touchpoints: ['Website', 'Reviews'] },
          { name: 'Purchase', description: 'Customer makes a decision', touchpoints: ['Checkout', 'Support'] }
        ]
      }
    }
    
    setPreviewData(sampleData[frameworkType.toLowerCase()] || sampleData.swot)
  }

  const filteredTemplates = templates.filter(template => {
    const categoryMatch = filterCategory === 'all' || template.category === filterCategory
    const frameworkMatch = template.framework_types.includes('all') || 
                           template.framework_types.includes(frameworkType.toLowerCase())
    return categoryMatch && frameworkMatch
  })

  const handleTemplateSelect = (template: Template) => {
    setSelectedTemplate(template)
    onSelectTemplate(template)
    onClose()
  }

  const renderPreview = (template: Template) => {
    if (!previewData) return null

    const styles = template.styles
    
    return (
      <div 
        className="w-full h-48 overflow-hidden rounded-lg relative"
        style={{ 
          background: styles.backgroundColor.includes('gradient') 
            ? styles.backgroundColor 
            : styles.backgroundColor,
          fontFamily: styles.fontFamily.includes('serif') ? 'Georgia, serif' : 
                     styles.fontFamily.includes('mono') ? 'Monaco, monospace' : 
                     'Inter, sans-serif'
        }}
      >
        <div className="p-4 h-full">
          {/* Header */}
          <div 
            className="mb-4"
            style={{ 
              color: styles.primaryColor,
              borderColor: styles.accentColor
            }}
          >
            <h3 className="text-lg font-bold">Sample Framework</h3>
          </div>
          
          {/* Content grid */}
          {frameworkType.toLowerCase().includes('swot') && (
            <div className="grid grid-cols-2 gap-2 h-32">
              {Object.entries(previewData).map(([key, values]: [string, any]) => (
                <div
                  key={key}
                  className={`p-2 text-xs ${styles.borderRadius}`}
                  style={{
                    backgroundColor: styles.backgroundColor.includes('gradient') 
                      ? 'rgba(255,255,255,0.1)' 
                      : '#f8f9fa',
                    border: `1px solid ${styles.accentColor}`,
                    color: styles.primaryColor
                  }}
                >
                  <div className="font-semibold mb-1 capitalize">{key}</div>
                  {values.slice(0, 2).map((item: string, index: number) => (
                    <div key={index} className="truncate">• {item}</div>
                  ))}
                </div>
              ))}
            </div>
          )}
          
          {frameworkType.toLowerCase().includes('canvas') && (
            <div className="grid grid-cols-3 gap-1 h-32">
              {Object.entries(previewData).slice(0, 6).map(([key, values]: [string, any]) => (
                <div
                  key={key}
                  className={`p-1 text-xs ${styles.borderRadius}`}
                  style={{
                    backgroundColor: styles.backgroundColor.includes('gradient') 
                      ? 'rgba(255,255,255,0.1)' 
                      : '#f8f9fa',
                    border: `1px solid ${styles.accentColor}`,
                    color: styles.primaryColor
                  }}
                >
                  <div className="font-semibold text-xs truncate">{key.replace(/_/g, ' ')}</div>
                </div>
              ))}
            </div>
          )}
          
          {frameworkType.toLowerCase().includes('journey') && (
            <div className="flex space-x-2 h-32">
              {previewData.stages?.slice(0, 3).map((stage: any, index: number) => (
                <div
                  key={index}
                  className={`flex-1 p-2 text-xs ${styles.borderRadius}`}
                  style={{
                    backgroundColor: styles.backgroundColor.includes('gradient') 
                      ? 'rgba(255,255,255,0.1)' 
                      : '#f8f9fa',
                    border: `1px solid ${styles.accentColor}`,
                    color: styles.primaryColor
                  }}
                >
                  <div className="font-semibold truncate">{stage.name}</div>
                  <div className="text-xs opacity-80 mt-1 truncate">{stage.description}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    )
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                Choose Template
              </h2>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                Select a design template for your {frameworkType} output
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Category Filter */}
          <div className="flex space-x-2 mt-4">
            {['all', 'business', 'modern', 'presentation', 'casual'].map(category => (
              <button
                key={category}
                onClick={() => setFilterCategory(category)}
                className={`px-3 py-1 rounded-full text-sm transition-colors ${
                  filterCategory === category
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                {category.charAt(0).toUpperCase() + category.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Templates Grid */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredTemplates.map(template => (
              <div
                key={template.id}
                className={`group cursor-pointer transition-all duration-200 ${
                  selectedTemplate?.id === template.id
                    ? 'ring-2 ring-blue-500 transform scale-105'
                    : 'hover:shadow-lg hover:transform hover:scale-105'
                }`}
                onClick={() => handleTemplateSelect(template)}
              >
                {/* Template Card */}
                <div className="bg-gray-50 dark:bg-gray-900 rounded-xl overflow-hidden border border-gray-200 dark:border-gray-700">
                  {/* Preview */}
                  <div className="h-48 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                    {renderPreview(template)}
                  </div>
                  
                  {/* Info */}
                  <div className="p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-semibold text-gray-900 dark:text-white">
                        {template.preview} {template.name}
                      </h3>
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        template.category === 'business' ? 'bg-blue-100 text-blue-800' :
                        template.category === 'modern' ? 'bg-purple-100 text-purple-800' :
                        template.category === 'presentation' ? 'bg-green-100 text-green-800' :
                        'bg-orange-100 text-orange-800'
                      }`}>
                        {template.category}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                      {template.description}
                    </p>
                    
                    {/* Features */}
                    <div className="flex flex-wrap gap-1">
                      <span className="px-2 py-1 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 text-xs rounded">
                        {template.styles.fontFamily.replace('font-', '')}
                      </span>
                      <span className="px-2 py-1 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 text-xs rounded">
                        {template.styles.gridLayout}
                      </span>
                      {template.styles.shadows && (
                        <span className="px-2 py-1 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 text-xs rounded">
                          shadows
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {filteredTemplates.length === 0 && (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">🎨</div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                No templates found
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Try adjusting your category filter or framework type
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-750">
          <div className="flex justify-between items-center">
            <div className="text-sm text-gray-500 dark:text-gray-400">
              {filteredTemplates.length} template{filteredTemplates.length !== 1 ? 's' : ''} available
            </div>
            <div className="flex space-x-3">
              <button
                onClick={onClose}
                className="px-4 py-2 text-gray-700 dark:text-gray-300 bg-gray-200 dark:bg-gray-700 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
              >
                Cancel
              </button>
              {selectedTemplate && (
                <button
                  onClick={() => handleTemplateSelect(selectedTemplate)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Apply Template
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}