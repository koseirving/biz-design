'use client'

import React, { useEffect, useRef, ReactNode } from 'react'
import { getFocusableElements } from './AccessibilityProvider'

interface FocusTrapProps {
  children: ReactNode
  active?: boolean
  restoreFocus?: boolean
  initialFocus?: string // Element ID or selector
  className?: string
}

export function FocusTrap({ 
  children, 
  active = true, 
  restoreFocus = true, 
  initialFocus,
  className = '' 
}: FocusTrapProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const previouslyFocusedElement = useRef<HTMLElement | null>(null)
  
  useEffect(() => {
    if (!active) return
    
    const container = containerRef.current
    if (!container) return
    
    // Store the previously focused element
    previouslyFocusedElement.current = document.activeElement as HTMLElement
    
    // Focus initial element or first focusable element
    const focusInitialElement = () => {
      let elementToFocus: HTMLElement | null = null
      
      if (initialFocus) {
        // Try to find element by ID first, then by selector
        elementToFocus = document.getElementById(initialFocus) ||
                        container.querySelector(initialFocus) as HTMLElement
      }
      
      if (!elementToFocus) {
        // Find first focusable element in container
        const focusableElements = getFocusableElements(container)
        elementToFocus = focusableElements[0] as HTMLElement
      }
      
      if (elementToFocus) {
        elementToFocus.focus()
      }
    }
    
    // Small delay to ensure DOM is ready
    const focusTimeout = setTimeout(focusInitialElement, 100)
    
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== 'Tab') return
      
      const focusableElements = getFocusableElements(container)
      if (focusableElements.length === 0) return
      
      const firstElement = focusableElements[0] as HTMLElement
      const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement
      
      if (event.shiftKey) {
        // Shift + Tab: moving backwards
        if (document.activeElement === firstElement) {
          event.preventDefault()
          lastElement.focus()
        }
      } else {
        // Tab: moving forwards
        if (document.activeElement === lastElement) {
          event.preventDefault()
          firstElement.focus()
        }
      }
    }
    
    // Add event listener
    document.addEventListener('keydown', handleKeyDown)
    
    return () => {
      clearTimeout(focusTimeout)
      document.removeEventListener('keydown', handleKeyDown)
      
      // Restore focus to previously focused element
      if (restoreFocus && previouslyFocusedElement.current) {
        previouslyFocusedElement.current.focus()
      }
    }
  }, [active, initialFocus, restoreFocus])
  
  if (!active) {
    return <>{children}</>
  }
  
  return (
    <div
      ref={containerRef}
      className={className}
    >
      {children}
    </div>
  )
}

export default FocusTrap