'use client';

import React, { useEffect, useRef, ReactNode } from 'react';

// Props for FocusTrap component
interface FocusTrapProps {
  children: ReactNode;
  active: boolean;
  restoreFocus?: boolean;
  focusFirstOnMount?: boolean;
  className?: string;
}

// Query selector for focusable elements
const FOCUSABLE_ELEMENTS = [
  'a[href]',
  'area[href]',
  'input:not([disabled]):not([type="hidden"]):not([aria-hidden])',
  'select:not([disabled]):not([aria-hidden])',
  'textarea:not([disabled]):not([aria-hidden])',
  'button:not([disabled]):not([aria-hidden])',
  'iframe',
  'object',
  'embed',
  '[contenteditable]',
  '[tabindex]:not([tabindex^="-"])',
].join(',');

// FocusTrap component
export function FocusTrap({
  children,
  active,
  restoreFocus = true,
  focusFirstOnMount = true,
  className = '',
}: FocusTrapProps): JSX.Element {
  const containerRef = useRef<HTMLDivElement>(null);
  const previouslyFocusedElement = useRef<HTMLElement | null>(null);
  const firstFocusableElement = useRef<HTMLElement | null>(null);
  const lastFocusableElement = useRef<HTMLElement | null>(null);

  // Get all focusable elements within the container
  const getFocusableElements = (): HTMLElement[] => {
    if (!containerRef.current) return [];
    
    const elements = containerRef.current.querySelectorAll(FOCUSABLE_ELEMENTS);
    return Array.from(elements).filter((element) => {
      const htmlElement = element as HTMLElement;
      
      // Check if element is visible and not hidden
      const style = window.getComputedStyle(htmlElement);
      if (
        style.display === 'none' ||
        style.visibility === 'hidden' ||
        htmlElement.offsetWidth === 0 ||
        htmlElement.offsetHeight === 0
      ) {
        return false;
      }

      // Check if element is not disabled
      if (htmlElement.hasAttribute('disabled')) {
        return false;
      }

      // Check if element has negative tabindex
      const tabIndex = htmlElement.getAttribute('tabindex');
      if (tabIndex && parseInt(tabIndex, 10) < 0) {
        return false;
      }

      return true;
    }) as HTMLElement[];
  };

  // Update focusable elements references
  const updateFocusableElements = () => {
    const focusableElements = getFocusableElements();
    firstFocusableElement.current = focusableElements[0] || null;
    lastFocusableElement.current = focusableElements[focusableElements.length - 1] || null;
  };

  // Handle keyboard navigation
  const handleKeyDown = (event: KeyboardEvent) => {
    if (!active || event.key !== 'Tab') return;

    updateFocusableElements();

    const { shiftKey } = event;
    const activeElement = document.activeElement as HTMLElement;

    // If no focusable elements, prevent default
    if (!firstFocusableElement.current || !lastFocusableElement.current) {
      event.preventDefault();
      return;
    }

    // Forward tab: if focused on last element, focus first
    if (!shiftKey && activeElement === lastFocusableElement.current) {
      event.preventDefault();
      firstFocusableElement.current.focus();
      return;
    }

    // Backward tab: if focused on first element, focus last
    if (shiftKey && activeElement === firstFocusableElement.current) {
      event.preventDefault();
      lastFocusableElement.current.focus();
      return;
    }

    // If focus is outside the container, move to first element
    if (containerRef.current && !containerRef.current.contains(activeElement)) {
      event.preventDefault();
      firstFocusableElement.current.focus();
    }
  };

  // Handle focus trap activation
  useEffect(() => {
    if (!active) return;

    // Store previously focused element
    previouslyFocusedElement.current = document.activeElement as HTMLElement;

    // Focus first element on mount
    if (focusFirstOnMount) {
      const timer = setTimeout(() => {
        updateFocusableElements();
        if (firstFocusableElement.current) {
          firstFocusableElement.current.focus();
        }
      }, 0);

      return () => clearTimeout(timer);
    }
  }, [active, focusFirstOnMount]);

  // Handle focus trap deactivation
  useEffect(() => {
    if (active) return;

    // Restore focus to previously focused element
    if (restoreFocus && previouslyFocusedElement.current) {
      const timer = setTimeout(() => {
        if (previouslyFocusedElement.current) {
          previouslyFocusedElement.current.focus();
        }
      }, 0);

      return () => clearTimeout(timer);
    }
  }, [active, restoreFocus]);

  // Add/remove event listeners
  useEffect(() => {
    if (active) {
      document.addEventListener('keydown', handleKeyDown);
      
      // Ensure focus stays within trap on click
      const handleClick = (event: MouseEvent) => {
        if (
          containerRef.current &&
          !containerRef.current.contains(event.target as Node)
        ) {
          updateFocusableElements();
          if (firstFocusableElement.current) {
            firstFocusableElement.current.focus();
          }
        }
      };

      document.addEventListener('click', handleClick, true);

      return () => {
        document.removeEventListener('keydown', handleKeyDown);
        document.removeEventListener('click', handleClick, true);
      };
    }
  }, [active]);

  // Focus management when container content changes
  useEffect(() => {
    if (active) {
      const observer = new MutationObserver(() => {
        updateFocusableElements();
      });

      if (containerRef.current) {
        observer.observe(containerRef.current, {
          childList: true,
          subtree: true,
          attributes: true,
          attributeFilter: ['tabindex', 'disabled', 'hidden', 'aria-hidden'],
        });
      }

      return () => observer.disconnect();
    }
  }, [active]);

  return (
    <div
      ref={containerRef}
      className={`focus-trap ${active ? 'focus-trap-active' : ''} ${className}`}
      data-focus-trap={active}
    >
      {/* Sentinel elements to catch focus escaping */}
      {active && (
        <>
          <div
            tabIndex={0}
            onFocus={() => {
              updateFocusableElements();
              if (lastFocusableElement.current) {
                lastFocusableElement.current.focus();
              }
            }}
            style={{
              position: 'absolute',
              left: '-9999px',
              top: '-9999px',
              width: '1px',
              height: '1px',
              opacity: 0,
              pointerEvents: 'none',
            }}
            aria-hidden="true"
          />
        </>
      )}
      
      {children}
      
      {active && (
        <>
          <div
            tabIndex={0}
            onFocus={() => {
              updateFocusableElements();
              if (firstFocusableElement.current) {
                firstFocusableElement.current.focus();
              }
            }}
            style={{
              position: 'absolute',
              left: '-9999px',
              top: '-9999px',
              width: '1px',
              height: '1px',
              opacity: 0,
              pointerEvents: 'none',
            }}
            aria-hidden="true"
          />
        </>
      )}
    </div>
  );
}

// Higher-order component for easy wrapping
export function withFocusTrap<P extends object>(
  Component: React.ComponentType<P>,
  options: Partial<FocusTrapProps> = {}
) {
  const WrappedComponent = (props: P & { focusTrapActive?: boolean }) => {
    const { focusTrapActive = true, ...componentProps } = props;
    
    return (
      <FocusTrap active={focusTrapActive} {...options}>
        <Component {...(componentProps as P)} />
      </FocusTrap>
    );
  };

  WrappedComponent.displayName = `withFocusTrap(${Component.displayName || Component.name})`;
  
  return WrappedComponent;
}

// Hook for programmatic focus management
export function useFocusTrap() {
  const trapRef = useRef<HTMLDivElement>(null);

  const focusFirst = () => {
    if (trapRef.current) {
      const firstFocusable = trapRef.current.querySelector(FOCUSABLE_ELEMENTS) as HTMLElement;
      if (firstFocusable) {
        firstFocusable.focus();
      }
    }
  };

  const focusLast = () => {
    if (trapRef.current) {
      const focusables = trapRef.current.querySelectorAll(FOCUSABLE_ELEMENTS);
      const lastFocusable = focusables[focusables.length - 1] as HTMLElement;
      if (lastFocusable) {
        lastFocusable.focus();
      }
    }
  };

  return {
    trapRef,
    focusFirst,
    focusLast,
  };
}

export default FocusTrap;