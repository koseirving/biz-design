'use client'

import React, { ReactNode } from 'react'

interface ScreenReaderTextProps {
  children: ReactNode
  as?: keyof JSX.IntrinsicElements
  className?: string
}

export function ScreenReaderText({ 
  children, 
  as: Component = 'span',
  className = '' 
}: ScreenReaderTextProps) {
  return (
    <Component className={`sr-only ${className}`}>
      {children}
    </Component>
  )
}

// Alternative component for when you need screen reader text to be visible in certain conditions
interface ConditionalScreenReaderTextProps {
  children: ReactNode
  showOnFocus?: boolean
  showOnHover?: boolean
  as?: keyof JSX.IntrinsicElements
  className?: string
}

export function ConditionalScreenReaderText({
  children,
  showOnFocus = false,
  showOnHover = false,
  as: Component = 'span',
  className = ''
}: ConditionalScreenReaderTextProps) {
  let classes = 'sr-only'
  
  if (showOnFocus) {
    classes += ' focus:not-sr-only focus:absolute focus:top-0 focus:left-0 focus:bg-white focus:text-black focus:p-2 focus:z-50'
  }
  
  if (showOnHover) {
    classes += ' hover:not-sr-only hover:absolute hover:top-0 hover:left-0 hover:bg-white hover:text-black hover:p-2 hover:z-50'
  }
  
  return (
    <Component className={`${classes} ${className}`}>
      {children}
    </Component>
  )
}

export default ScreenReaderText