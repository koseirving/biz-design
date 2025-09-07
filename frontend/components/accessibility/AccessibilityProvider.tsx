'use client'

import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react'
import { useLocalStorage } from '@/hooks/useLocalStorage'

// Accessibility preference types
export interface AccessibilityPreferences {
  // Visual preferences
  highContrast: boolean
  largeText: boolean
  reducedMotion: boolean
  darkMode: boolean
  
  // Keyboard navigation
  keyboardNavigation: boolean
  focusVisible: boolean
  skipLinks: boolean
  
  // Screen reader support
  screenReader: boolean
  announceChanges: boolean
  verboseLabels: boolean
  
  // Other preferences
  autoplay: boolean
  soundEnabled: boolean
  hapticFeedback: boolean
}

// Action types for accessibility reducer
type AccessibilityAction =
  | { type: 'SET_PREFERENCE'; key: keyof AccessibilityPreferences; value: boolean }
  | { type: 'RESET_PREFERENCES' }
  | { type: 'LOAD_PREFERENCES'; preferences: Partial<AccessibilityPreferences> }
  | { type: 'DETECT_SYSTEM_PREFERENCES' }

// Default accessibility preferences
const defaultPreferences: AccessibilityPreferences = {
  highContrast: false,
  largeText: false,
  reducedMotion: false,
  darkMode: false,
  keyboardNavigation: true,
  focusVisible: true,
  skipLinks: true,
  screenReader: false,
  announceChanges: true,
  verboseLabels: false,
  autoplay: false,
  soundEnabled: true,
  hapticFeedback: true,
}

// Accessibility context
interface AccessibilityContextType {
  preferences: AccessibilityPreferences
  setPreference: (key: keyof AccessibilityPreferences, value: boolean) => void
  resetPreferences: () => void
  announceToScreenReader: (message: string, priority?: 'polite' | 'assertive') => void
  focusElement: (elementId: string) => void
  skipToContent: () => void
}

const AccessibilityContext = createContext<AccessibilityContextType | undefined>(undefined)

// Reducer for accessibility state management
function accessibilityReducer(
  state: AccessibilityPreferences,
  action: AccessibilityAction
): AccessibilityPreferences {
  switch (action.type) {
    case 'SET_PREFERENCE':
      return {
        ...state,
        [action.key]: action.value,
      }
    
    case 'RESET_PREFERENCES':
      return { ...defaultPreferences }
    
    case 'LOAD_PREFERENCES':
      return {
        ...state,
        ...action.preferences,
      }
    
    case 'DETECT_SYSTEM_PREFERENCES':
      return {
        ...state,
        reducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches,
        darkMode: window.matchMedia('(prefers-color-scheme: dark)').matches,
        highContrast: window.matchMedia('(prefers-contrast: high)').matches,
      }
    
    default:
      return state
  }
}

interface AccessibilityProviderProps {
  children: ReactNode
}

export function AccessibilityProvider({ children }: AccessibilityProviderProps) {
  const [storedPreferences, setStoredPreferences] = useLocalStorage<Partial<AccessibilityPreferences>>(
    'accessibility-preferences',
    {}
  )
  
  const [preferences, dispatch] = useReducer(accessibilityReducer, defaultPreferences)
  
  // Load preferences from localStorage on mount
  useEffect(() => {
    if (storedPreferences && Object.keys(storedPreferences).length > 0) {
      dispatch({ type: 'LOAD_PREFERENCES', preferences: storedPreferences })
    }
    
    // Detect system accessibility preferences
    dispatch({ type: 'DETECT_SYSTEM_PREFERENCES' })
  }, [storedPreferences])
  
  // Apply CSS classes and variables based on preferences
  useEffect(() => {
    const root = document.documentElement
    
    // High contrast mode
    if (preferences.highContrast) {
      root.classList.add('accessibility-high-contrast')
    } else {
      root.classList.remove('accessibility-high-contrast')
    }
    
    // Large text mode
    if (preferences.largeText) {
      root.classList.add('accessibility-large-text')
    } else {
      root.classList.remove('accessibility-large-text')
    }
    
    // Reduced motion
    if (preferences.reducedMotion) {
      root.classList.add('accessibility-reduced-motion')
    } else {
      root.classList.remove('accessibility-reduced-motion')
    }
    
    // Focus visible
    if (preferences.focusVisible) {
      root.classList.add('accessibility-focus-visible')
    } else {
      root.classList.remove('accessibility-focus-visible')
    }
    
    // Keyboard navigation
    if (preferences.keyboardNavigation) {
      root.classList.add('accessibility-keyboard-nav')
    } else {
      root.classList.remove('accessibility-keyboard-nav')
    }
    
    // Screen reader optimizations
    if (preferences.screenReader) {
      root.classList.add('accessibility-screen-reader')
    } else {
      root.classList.remove('accessibility-screen-reader')
    }
    
  }, [preferences])
  
  // Set up media query listeners for system preference changes
  useEffect(() => {
    const mediaQueries = [
      {
        query: '(prefers-reduced-motion: reduce)',
        handler: (matches: boolean) => {
          if (matches !== preferences.reducedMotion) {
            dispatch({ type: 'SET_PREFERENCE', key: 'reducedMotion', value: matches })
          }
        }
      },
      {
        query: '(prefers-color-scheme: dark)',
        handler: (matches: boolean) => {
          if (matches !== preferences.darkMode) {
            dispatch({ type: 'SET_PREFERENCE', key: 'darkMode', value: matches })
          }
        }
      },
      {
        query: '(prefers-contrast: high)',
        handler: (matches: boolean) => {
          if (matches !== preferences.highContrast) {
            dispatch({ type: 'SET_PREFERENCE', key: 'highContrast', value: matches })
          }
        }
      }
    ]
    
    const mediaQueryLists = mediaQueries.map(({ query, handler }) => {
      const mql = window.matchMedia(query)
      const listener = (e: MediaQueryListEvent) => handler(e.matches)
      mql.addListener(listener)
      return { mql, listener }
    })
    
    return () => {
      mediaQueryLists.forEach(({ mql, listener }) => {
        mql.removeListener(listener)
      })
    }
  }, [preferences])
  
  // Set up keyboard navigation
  useEffect(() => {
    if (!preferences.keyboardNavigation) return
    
    const handleKeyDown = (event: KeyboardEvent) => {
      // Skip to content with Alt+S or Ctrl+/
      if ((event.altKey && event.key === 's') || (event.ctrlKey && event.key === '/')) {
        event.preventDefault()
        skipToContent()
        return
      }
      
      // Focus management with Tab navigation
      if (event.key === 'Tab') {
        // Ensure focus is visible when using keyboard
        document.body.classList.add('keyboard-navigation-active')
      }
      
      // Escape key handling for modals and overlays
      if (event.key === 'Escape') {
        // Close any open modals or overlays
        const activeElement = document.activeElement as HTMLElement
        if (activeElement?.closest('[role=\"dialog\"]') || activeElement?.closest('.modal')) {
          event.preventDefault()
          // Find and click close button or trigger escape handler
          const closeButton = activeElement.closest('[role=\"dialog\"], .modal')?.querySelector('[aria-label*=\"close\"], [data-close]') as HTMLElement
          if (closeButton) {
            closeButton.click()
          }
        }
      }
    }
    
    const handleMouseDown = () => {
      // Remove keyboard navigation styling when using mouse
      document.body.classList.remove('keyboard-navigation-active')
    }
    
    document.addEventListener('keydown', handleKeyDown)
    document.addEventListener('mousedown', handleMouseDown)
    
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.removeEventListener('mousedown', handleMouseDown)
    }
  }, [preferences.keyboardNavigation])
  
  // Context functions
  const setPreference = (key: keyof AccessibilityPreferences, value: boolean) => {
    dispatch({ type: 'SET_PREFERENCE', key, value })
    
    // Update localStorage
    const updatedPreferences = {
      ...storedPreferences,
      [key]: value,
    }
    setStoredPreferences(updatedPreferences)
  }
  
  const resetPreferences = () => {
    dispatch({ type: 'RESET_PREFERENCES' })
    setStoredPreferences({})
  }
  
  const announceToScreenReader = (message: string, priority: 'polite' | 'assertive' = 'polite') => {
    if (!preferences.announceChanges) return
    
    // Create or update live region
    let liveRegion = document.getElementById('accessibility-live-region')
    
    if (!liveRegion) {
      liveRegion = document.createElement('div')
      liveRegion.id = 'accessibility-live-region'
      liveRegion.setAttribute('aria-live', priority)
      liveRegion.setAttribute('aria-atomic', 'true')
      liveRegion.className = 'sr-only'
      document.body.appendChild(liveRegion)
    } else {
      liveRegion.setAttribute('aria-live', priority)
    }
    
    // Clear and set new message
    liveRegion.textContent = ''
    setTimeout(() => {
      liveRegion!.textContent = message
    }, 100)
    
    // Clear message after announcement
    setTimeout(() => {
      liveRegion!.textContent = ''
    }, 5000)
  }
  
  const focusElement = (elementId: string) => {
    const element = document.getElementById(elementId)
    if (element) {
      element.focus()
      
      // Announce focus change to screen readers
      const elementLabel = element.getAttribute('aria-label') || 
                          element.getAttribute('title') || 
                          element.textContent ||
                          'Element'
      
      announceToScreenReader(`Focused on ${elementLabel}`)
    }
  }
  
  const skipToContent = () => {
    const mainContent = document.getElementById('main-content') || 
                       document.querySelector('main') ||
                       document.querySelector('[role=\"main\"]') as HTMLElement
    
    if (mainContent) {
      mainContent.focus()
      mainContent.scrollIntoView({ behavior: 'smooth' })
      announceToScreenReader('Skipped to main content')
    }
  }
  
  const contextValue: AccessibilityContextType = {
    preferences,
    setPreference,
    resetPreferences,
    announceToScreenReader,
    focusElement,
    skipToContent,
  }
  
  return (
    <AccessibilityContext.Provider value={contextValue}>
      {children}
      
      {/* Skip links (visible when focused) */}
      {preferences.skipLinks && (
        <div className=\"skip-links\">
          <button
            className=\"skip-link\"
            onClick={skipToContent}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault()
                skipToContent()
              }
            }}
          >
            Skip to main content
          </button>
        </div>
      )}
      
      {/* Screen reader live region */}
      <div
        id=\"accessibility-live-region\"
        aria-live=\"polite\"
        aria-atomic=\"true\"
        className=\"sr-only\"
      />
      
      {/* Focus trap for modals (when needed) */}
      <div id=\"focus-trap-anchor\" tabIndex={-1} />
    </AccessibilityContext.Provider>
  )
}

// Custom hook to use accessibility context
export function useAccessibility() {
  const context = useContext(AccessibilityContext)
  if (context === undefined) {
    throw new Error('useAccessibility must be used within an AccessibilityProvider')
  }
  return context
}

// HOC for accessibility enhancements
export function withAccessibility<P extends object>(Component: React.ComponentType<P>) {
  return function AccessibleComponent(props: P) {
    const accessibility = useAccessibility()
    
    return (
      <Component
        {...props}
        accessibility={accessibility}
      />
    )
  }
}

// Utility function to generate accessible IDs
export function generateAccessibleId(prefix: string = 'accessible'): string {
  return `${prefix}-${Math.random().toString(36).substr(2, 9)}`
}

// Utility function to check if element is focusable
export function isFocusable(element: Element): boolean {
  const focusableElements = [
    'a[href]',
    'button:not([disabled])',
    'input:not([disabled])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    '[tabindex]:not([tabindex=\"-1\"])',
    '[contenteditable]'
  ]
  
  return focusableElements.some(selector => element.matches(selector))
}

// Utility function to get all focusable elements within a container
export function getFocusableElements(container: Element): Element[] {
  const focusableSelectors = [
    'a[href]',
    'button:not([disabled])',
    'input:not([disabled])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    '[tabindex]:not([tabindex=\"-1\"])',
    '[contenteditable]'
  ].join(', ')
  
  return Array.from(container.querySelectorAll(focusableSelectors))
}

export default AccessibilityProvider