'use client'

import React, { useState, useEffect } from 'react'
import { useAccessibility } from './AccessibilityProvider'
import { 
  Settings, 
  Eye, 
  Type, 
  Zap,
  Moon,
  Sun,
  Keyboard,
  Target,
  Volume2,
  VolumeX,
  RotateCcw
} from 'lucide-react'

interface AccessibilityMenuProps {
  className?: string
}

export function AccessibilityMenu({ className = '' }: AccessibilityMenuProps) {
  const {
    preferences,
    setPreference,
    resetPreferences,
    announceToScreenReader
  } = useAccessibility()
  
  const [isOpen, setIsOpen] = useState(false)
  const [activeSection, setActiveSection] = useState<string>('visual')
  
  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Element
      if (!target.closest('.accessibility-menu')) {
        setIsOpen(false)
      }
    }
    
    if (isOpen) {
      document.addEventListener('click', handleClickOutside)
      return () => document.removeEventListener('click', handleClickOutside)
    }
  }, [isOpen])
  
  // Keyboard navigation for menu
  useEffect(() => {
    if (!isOpen) return
    
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false)
        announceToScreenReader('Accessibility menu closed')
      }
    }
    
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, announceToScreenReader])
  
  const toggleMenu = () => {
    const newState = !isOpen
    setIsOpen(newState)
    announceToScreenReader(
      newState ? 'Accessibility menu opened' : 'Accessibility menu closed'
    )
  }
  
  const handlePreferenceChange = (key: keyof typeof preferences, value: boolean, description: string) => {
    setPreference(key, value)
    announceToScreenReader(
      `${description} ${value ? 'enabled' : 'disabled'}`
    )
  }
  
  const handleReset = () => {
    resetPreferences()
    announceToScreenReader('Accessibility preferences reset to defaults')
  }
  
  const menuSections = [
    {
      id: 'visual',
      title: 'Visual',
      icon: <Eye className=\"w-4 h-4\" />,
      preferences: [
        {
          key: 'highContrast' as const,
          title: 'High Contrast',
          description: 'Increase color contrast for better visibility',
          icon: <Target className=\"w-4 h-4\" />
        },
        {
          key: 'largeText' as const,
          title: 'Large Text',
          description: 'Increase text size throughout the application',
          icon: <Type className=\"w-4 h-4\" />
        },
        {
          key: 'reducedMotion' as const,
          title: 'Reduced Motion',
          description: 'Minimize animations and transitions',
          icon: <Zap className=\"w-4 h-4\" />
        },
        {
          key: 'darkMode' as const,
          title: 'Dark Mode',
          description: 'Use dark theme for reduced eye strain',
          icon: preferences.darkMode ? <Moon className=\"w-4 h-4\" /> : <Sun className=\"w-4 h-4\" />
        }
      ]
    },
    {
      id: 'navigation',
      title: 'Navigation',
      icon: <Keyboard className=\"w-4 h-4\" />,
      preferences: [
        {
          key: 'keyboardNavigation' as const,
          title: 'Keyboard Navigation',
          description: 'Enable full keyboard navigation support',
          icon: <Keyboard className=\"w-4 h-4\" />
        },
        {
          key: 'focusVisible' as const,
          title: 'Focus Indicators',
          description: 'Show clear focus indicators for keyboard users',
          icon: <Target className=\"w-4 h-4\" />
        },
        {
          key: 'skipLinks' as const,
          title: 'Skip Links',
          description: 'Enable skip navigation links',
          icon: <Zap className=\"w-4 h-4\" />
        }
      ]
    },
    {
      id: 'audio',
      title: 'Audio & Feedback',
      icon: <Volume2 className=\"w-4 h-4\" />,
      preferences: [
        {
          key: 'soundEnabled' as const,
          title: 'Sound Effects',
          description: 'Enable audio feedback and sound effects',
          icon: preferences.soundEnabled ? <Volume2 className=\"w-4 h-4\" /> : <VolumeX className=\"w-4 h-4\" />
        },
        {
          key: 'announceChanges' as const,
          title: 'Screen Reader Announcements',
          description: 'Announce important changes to screen readers',
          icon: <Volume2 className=\"w-4 h-4\" />
        },
        {
          key: 'hapticFeedback' as const,
          title: 'Haptic Feedback',
          description: 'Enable vibration feedback on supported devices',
          icon: <Zap className=\"w-4 h-4\" />
        }
      ]
    }
  ]
  
  return (
    <div className={`accessibility-menu relative ${className}`}>
      {/* Accessibility Menu Toggle Button */}
      <button
        onClick={toggleMenu}
        className=\"accessibility-menu-toggle p-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500\"
        aria-label=\"Open accessibility settings\"
        aria-expanded={isOpen}
        aria-haspopup=\"dialog\"
      >
        <Settings className=\"w-5 h-5 text-gray-700 dark:text-gray-300\" />
      </button>
      
      {/* Accessibility Menu Panel */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div 
            className=\"fixed inset-0 bg-black bg-opacity-25 z-40\"
            onClick={() => setIsOpen(false)}
            aria-hidden=\"true\"
          />
          
          {/* Menu Panel */}
          <div
            className=\"absolute right-0 top-12 w-80 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-50\"
            role=\"dialog\"
            aria-modal=\"true\"
            aria-labelledby=\"accessibility-menu-title\"
          >
            {/* Header */}
            <div className=\"p-4 border-b border-gray-200 dark:border-gray-700\">
              <div className=\"flex items-center justify-between\">
                <h2 
                  id=\"accessibility-menu-title\"
                  className=\"text-lg font-semibold text-gray-900 dark:text-gray-100\"
                >
                  Accessibility Settings
                </h2>
                <button
                  onClick={() => setIsOpen(false)}
                  className=\"p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500\"
                  aria-label=\"Close accessibility menu\"
                >
                  <span className=\"sr-only\">Close</span>
                  <svg className=\"w-5 h-5\" fill=\"none\" stroke=\"currentColor\" viewBox=\"0 0 24 24\">
                    <path strokeLinecap=\"round\" strokeLinejoin=\"round\" strokeWidth={2} d=\"M6 18L18 6M6 6l12 12\" />
                  </svg>
                </button>
              </div>
              
              {/* Section Tabs */}
              <div className=\"flex space-x-1 mt-3\" role=\"tablist\" aria-label=\"Accessibility categories\">
                {menuSections.map((section) => (
                  <button
                    key={section.id}
                    role=\"tab\"
                    tabIndex={activeSection === section.id ? 0 : -1}
                    aria-selected={activeSection === section.id}
                    aria-controls={`${section.id}-panel`}
                    className={`flex items-center px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                      activeSection === section.id
                        ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300'
                        : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700'
                    }`}
                    onClick={() => {
                      setActiveSection(section.id)
                      announceToScreenReader(`${section.title} settings selected`)
                    }}
                  >
                    {section.icon}
                    <span className=\"ml-2\">{section.title}</span>
                  </button>
                ))}
              </div>
            </div>
            
            {/* Content */}
            <div className=\"p-4 max-h-80 overflow-y-auto\">
              {menuSections.map((section) => (
                <div
                  key={section.id}
                  id={`${section.id}-panel`}
                  role=\"tabpanel\"
                  aria-labelledby={`${section.id}-tab`}
                  className={activeSection === section.id ? 'block' : 'hidden'}
                >
                  <div className=\"space-y-4\">
                    {section.preferences.map((pref) => (
                      <div key={pref.key} className=\"flex items-start space-x-3\">
                        <div className=\"flex-shrink-0 mt-1\">
                          {pref.icon}
                        </div>
                        <div className=\"flex-1\">
                          <label className=\"flex items-center cursor-pointer\">
                            <input
                              type=\"checkbox\"
                              checked={preferences[pref.key]}
                              onChange={(e) => 
                                handlePreferenceChange(
                                  pref.key, 
                                  e.target.checked, 
                                  pref.title
                                )
                              }
                              className=\"sr-only\"
                            />
                            <div className=\"relative flex items-center\">
                              <div className={`w-5 h-5 rounded border-2 transition-colors ${
                                preferences[pref.key]
                                  ? 'bg-blue-600 border-blue-600'
                                  : 'bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600'
                              }`}>
                                {preferences[pref.key] && (
                                  <svg 
                                    className=\"w-3 h-3 text-white absolute top-0.5 left-0.5\" 
                                    fill=\"currentColor\" 
                                    viewBox=\"0 0 20 20\"
                                  >
                                    <path 
                                      fillRule=\"evenodd\" 
                                      d=\"M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z\" 
                                      clipRule=\"evenodd\" 
                                    />
                                  </svg>
                                )}
                              </div>
                              <div className=\"ml-3\">
                                <div className=\"text-sm font-medium text-gray-900 dark:text-gray-100\">
                                  {pref.title}
                                </div>
                                <div className=\"text-xs text-gray-500 dark:text-gray-400\">
                                  {pref.description}
                                </div>
                              </div>
                            </div>
                          </label>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
            
            {/* Footer */}
            <div className=\"p-4 border-t border-gray-200 dark:border-gray-700\">
              <button
                onClick={handleReset}
                className=\"flex items-center justify-center w-full px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors\"
              >
                <RotateCcw className=\"w-4 h-4 mr-2\" />
                Reset to Defaults
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default AccessibilityMenu