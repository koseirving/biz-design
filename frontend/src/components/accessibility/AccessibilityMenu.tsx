'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useAccessibility } from './AccessibilityProvider';

// AccessibilityMenu component
export function AccessibilityMenu(): JSX.Element {
  const { settings, updateSetting, resetSettings, announceToScreenReader } = useAccessibility();
  const [isOpen, setIsOpen] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const toggleButtonRef = useRef<HTMLButtonElement>(null);

  // Handle escape key to close menu
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isOpen) {
        setIsOpen(false);
        toggleButtonRef.current?.focus();
      }
    };

    const handleClickOutside = (event: MouseEvent) => {
      if (
        menuRef.current &&
        !menuRef.current.contains(event.target as Node) &&
        !toggleButtonRef.current?.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  // Focus management when menu opens/closes
  useEffect(() => {
    if (isOpen && menuRef.current) {
      // Focus first focusable element in menu
      const firstFocusable = menuRef.current.querySelector(
        'button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
      ) as HTMLElement;
      if (firstFocusable) {
        setTimeout(() => firstFocusable.focus(), 100);
      }
    }
  }, [isOpen]);

  // Handle menu toggle
  const toggleMenu = () => {
    setIsAnimating(true);
    setIsOpen(prev => {
      const newState = !prev;
      announceToScreenReader(
        newState ? 'Accessibility menu opened' : 'Accessibility menu closed',
        'polite'
      );
      return newState;
    });

    setTimeout(() => setIsAnimating(false), 300);
  };

  // Handle setting change with keyboard support
  const handleSettingChange = (key: keyof typeof settings, value: boolean) => {
    updateSetting(key, value);
  };

  // Handle reset with confirmation
  const handleReset = () => {
    if (window.confirm('Reset all accessibility settings to default?')) {
      resetSettings();
    }
  };

  // Keyboard navigation within menu
  const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key === 'Tab') {
      const focusableElements = menuRef.current?.querySelectorAll(
        'button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      
      if (focusableElements && focusableElements.length > 0) {
        const firstElement = focusableElements[0] as HTMLElement;
        const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;
        
        if (event.shiftKey && document.activeElement === firstElement) {
          event.preventDefault();
          lastElement.focus();
        } else if (!event.shiftKey && document.activeElement === lastElement) {
          event.preventDefault();
          firstElement.focus();
        }
      }
    }
  };

  // Setting options configuration
  const settingOptions = [
    {
      key: 'highContrast' as const,
      label: 'High Contrast',
      description: 'Increase contrast for better visibility',
      value: settings.highContrast,
    },
    {
      key: 'largeText' as const,
      label: 'Large Text',
      description: 'Increase text size for better readability',
      value: settings.largeText,
    },
    {
      key: 'reducedMotion' as const,
      label: 'Reduce Motion',
      description: 'Minimize animations and transitions',
      value: settings.reducedMotion,
    },
    {
      key: 'focusVisible' as const,
      label: 'Enhanced Focus',
      description: 'Show clear focus indicators',
      value: settings.focusVisible,
    },
    {
      key: 'keyboardNavigation' as const,
      label: 'Keyboard Navigation',
      description: 'Optimize for keyboard-only navigation',
      value: settings.keyboardNavigation,
    },
    {
      key: 'screenReaderOptimizations' as const,
      label: 'Screen Reader',
      description: 'Optimize for screen reader users',
      value: settings.screenReaderOptimizations,
    },
  ];

  return (
    <div className="accessibility-widget">
      {/* Toggle Button */}
      <button
        ref={toggleButtonRef}
        onClick={toggleMenu}
        className={`
          fixed top-5 right-5 z-50
          w-12 h-12 
          bg-blue-600 hover:bg-blue-700 
          text-white rounded-full
          shadow-lg hover:shadow-xl
          transition-all duration-200
          focus:outline-none focus:ring-4 focus:ring-blue-300
          flex items-center justify-center
          ${isAnimating ? 'scale-95' : 'hover:scale-105'}
          ${isOpen ? 'bg-blue-700' : ''}
        `}
        aria-label={isOpen ? 'Close accessibility menu' : 'Open accessibility menu'}
        aria-expanded={isOpen}
        aria-controls="accessibility-menu"
        title="Accessibility Settings"
      >
        <svg
          className={`w-6 h-6 transition-transform duration-200 ${isOpen ? 'rotate-45' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4"
          />
        </svg>
      </button>

      {/* Menu Panel */}
      {isOpen && (
        <div
          ref={menuRef}
          id="accessibility-menu"
          className={`
            fixed top-20 right-5 z-40
            w-80 max-w-[calc(100vw-2.5rem)]
            bg-white dark:bg-gray-800
            border border-gray-200 dark:border-gray-700
            rounded-lg shadow-2xl
            p-6
            transition-all duration-300 ease-out
            ${isOpen ? 'opacity-100 scale-100' : 'opacity-0 scale-95'}
          `}
          role="dialog"
          aria-modal="true"
          aria-labelledby="accessibility-menu-title"
          onKeyDown={handleKeyDown}
        >
          {/* Header */}
          <div className="mb-6">
            <h3
              id="accessibility-menu-title"
              className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2"
            >
              Accessibility Settings
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Customize your viewing experience
            </p>
          </div>

          {/* Settings List */}
          <div className="space-y-4 mb-6">
            {settingOptions.map(({ key, label, description, value }) => (
              <div key={key} className="flex items-start justify-between">
                <div className="flex-1 mr-3">
                  <label
                    htmlFor={`accessibility-${key}`}
                    className="block text-sm font-medium text-gray-900 dark:text-gray-100 cursor-pointer"
                  >
                    {label}
                  </label>
                  <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                    {description}
                  </p>
                </div>
                <div className="flex-shrink-0">
                  <button
                    id={`accessibility-${key}`}
                    onClick={() => handleSettingChange(key, !value)}
                    className={`
                      relative inline-flex h-6 w-11 items-center rounded-full
                      transition-colors duration-200 ease-in-out
                      focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                      focus:ring-offset-white dark:focus:ring-offset-gray-800
                      ${value ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-700'}
                    `}
                    role="switch"
                    aria-checked={value}
                    aria-labelledby={`accessibility-${key}`}
                    aria-describedby={`accessibility-${key}-desc`}
                  >
                    <span className="sr-only">
                      {value ? 'Disable' : 'Enable'} {label}
                    </span>
                    <span
                      className={`
                        inline-block h-4 w-4 transform rounded-full
                        bg-white shadow-lg ring-0 transition-transform duration-200 ease-in-out
                        ${value ? 'translate-x-6' : 'translate-x-1'}
                      `}
                    />
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
            <button
              onClick={handleReset}
              className="
                flex-1 px-4 py-2
                bg-gray-100 hover:bg-gray-200
                dark:bg-gray-700 dark:hover:bg-gray-600
                text-gray-700 dark:text-gray-300
                text-sm font-medium rounded-md
                transition-colors duration-200
                focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2
                focus:ring-offset-white dark:focus:ring-offset-gray-800
              "
            >
              Reset All
            </button>
            <button
              onClick={() => setIsOpen(false)}
              className="
                flex-1 px-4 py-2
                bg-blue-600 hover:bg-blue-700
                text-white text-sm font-medium rounded-md
                transition-colors duration-200
                focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                focus:ring-offset-white dark:focus:ring-offset-gray-800
              "
            >
              Close
            </button>
          </div>

          {/* Screen Reader Instructions */}
          <div className="sr-only" aria-live="polite" role="status">
            Use Tab and Shift+Tab to navigate between settings.
            Press Space or Enter to toggle settings.
            Press Escape to close this menu.
          </div>
        </div>
      )}

      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-30 bg-black bg-opacity-25 transition-opacity duration-300"
          onClick={() => setIsOpen(false)}
          aria-hidden="true"
        />
      )}
    </div>
  );
}

export default AccessibilityMenu;