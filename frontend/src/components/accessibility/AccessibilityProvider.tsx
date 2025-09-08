'use client';

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';

// Accessibility settings interface
export interface AccessibilitySettings {
  highContrast: boolean;
  largeText: boolean;
  reducedMotion: boolean;
  focusVisible: boolean;
  keyboardNavigation: boolean;
  screenReaderOptimizations: boolean;
}

// Default accessibility settings
const defaultSettings: AccessibilitySettings = {
  highContrast: false,
  largeText: false,
  reducedMotion: false,
  focusVisible: true,
  keyboardNavigation: false,
  screenReaderOptimizations: false,
};

// Accessibility context interface
interface AccessibilityContextType {
  settings: AccessibilitySettings;
  updateSetting: (key: keyof AccessibilitySettings, value: boolean) => void;
  resetSettings: () => void;
  announceToScreenReader: (message: string, priority?: 'polite' | 'assertive') => void;
}

// Create accessibility context
const AccessibilityContext = createContext<AccessibilityContextType | undefined>(undefined);

// Custom hook to use accessibility context
export function useAccessibility(): AccessibilityContextType {
  const context = useContext(AccessibilityContext);
  if (context === undefined) {
    throw new Error('useAccessibility must be used within an AccessibilityProvider');
  }
  return context;
}

// Props for AccessibilityProvider
interface AccessibilityProviderProps {
  children: ReactNode;
}

// Local storage key for persisting settings
const STORAGE_KEY = 'accessibility-settings';

// AccessibilityProvider component
export function AccessibilityProvider({ children }: AccessibilityProviderProps): JSX.Element {
  const [settings, setSettings] = useState<AccessibilitySettings>(defaultSettings);
  const [liveRegionElement, setLiveRegionElement] = useState<HTMLElement | null>(null);

  // Load settings from localStorage on mount
  useEffect(() => {
    try {
      const savedSettings = localStorage.getItem(STORAGE_KEY);
      if (savedSettings) {
        const parsed = JSON.parse(savedSettings);
        setSettings({ ...defaultSettings, ...parsed });
      }
    } catch (error) {
      console.warn('Failed to load accessibility settings:', error);
    }
  }, []);

  // Create and setup live region for screen reader announcements
  useEffect(() => {
    const liveRegion = document.createElement('div');
    liveRegion.setAttribute('aria-live', 'polite');
    liveRegion.setAttribute('aria-atomic', 'true');
    liveRegion.className = 'sr-only live-region';
    liveRegion.id = 'accessibility-live-region';
    document.body.appendChild(liveRegion);
    setLiveRegionElement(liveRegion);

    // Cleanup on unmount
    return () => {
      if (document.body.contains(liveRegion)) {
        document.body.removeChild(liveRegion);
      }
    };
  }, []);

  // Apply accessibility settings to document
  useEffect(() => {
    const applySettings = () => {
      const { body } = document;
      const classList = body.classList;

      // Remove all accessibility classes
      const accessibilityClasses = [
        'accessibility-high-contrast',
        'accessibility-large-text',
        'accessibility-reduced-motion',
        'accessibility-focus-visible',
        'accessibility-keyboard-nav',
        'accessibility-screen-reader'
      ];
      
      accessibilityClasses.forEach(className => classList.remove(className));

      // Apply settings
      if (settings.highContrast) {
        classList.add('accessibility-high-contrast');
      }
      
      if (settings.largeText) {
        classList.add('accessibility-large-text');
      }
      
      if (settings.reducedMotion) {
        classList.add('accessibility-reduced-motion');
      }
      
      if (settings.focusVisible) {
        classList.add('accessibility-focus-visible');
      }
      
      if (settings.keyboardNavigation) {
        classList.add('accessibility-keyboard-nav');
        classList.add('keyboard-navigation-active');
      }
      
      if (settings.screenReaderOptimizations) {
        classList.add('accessibility-screen-reader');
      }

      // Handle prefers-reduced-motion media query
      if (settings.reducedMotion) {
        const style = document.createElement('style');
        style.id = 'accessibility-reduced-motion-override';
        style.textContent = `
          *, *::before, *::after {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
            scroll-behavior: auto !important;
          }
        `;
        document.head.appendChild(style);
      } else {
        const existingStyle = document.getElementById('accessibility-reduced-motion-override');
        if (existingStyle) {
          existingStyle.remove();
        }
      }
    };

    applySettings();
  }, [settings]);

  // Save settings to localStorage whenever they change
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    } catch (error) {
      console.warn('Failed to save accessibility settings:', error);
    }
  }, [settings]);

  // Handle keyboard navigation detection
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Tab') {
        updateSetting('keyboardNavigation', true);
      }
    };

    const handleMouseDown = () => {
      // Don't disable keyboard navigation on mouse use
      // Keep it enabled once user has used keyboard
    };

    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('mousedown', handleMouseDown);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('mousedown', handleMouseDown);
    };
  }, []);

  // Handle system preference changes
  useEffect(() => {
    const handleColorSchemeChange = (e: MediaQueryListEvent) => {
      // React to system color scheme changes if needed
      console.log('Color scheme changed:', e.matches ? 'dark' : 'light');
    };

    const handleMotionChange = (e: MediaQueryListEvent) => {
      if (e.matches && !settings.reducedMotion) {
        // User prefers reduced motion but hasn't enabled it
        announceToScreenReader(
          'Your system indicates you prefer reduced motion. You can enable this in the accessibility menu.',
          'polite'
        );
      }
    };

    const handleContrastChange = (e: MediaQueryListEvent) => {
      if (e.matches && !settings.highContrast) {
        // User prefers high contrast but hasn't enabled it
        announceToScreenReader(
          'Your system indicates you prefer high contrast. You can enable this in the accessibility menu.',
          'polite'
        );
      }
    };

    // Set up media query listeners
    const colorSchemeQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    const contrastQuery = window.matchMedia('(prefers-contrast: high)');

    colorSchemeQuery.addEventListener('change', handleColorSchemeChange);
    motionQuery.addEventListener('change', handleMotionChange);
    contrastQuery.addEventListener('change', handleContrastChange);

    return () => {
      colorSchemeQuery.removeEventListener('change', handleColorSchemeChange);
      motionQuery.removeEventListener('change', handleMotionChange);
      contrastQuery.removeEventListener('change', handleContrastChange);
    };
  }, [settings.reducedMotion, settings.highContrast]);

  // Function to update a single setting
  const updateSetting = (key: keyof AccessibilitySettings, value: boolean) => {
    setSettings(prevSettings => ({
      ...prevSettings,
      [key]: value
    }));

    // Announce setting changes to screen readers
    const settingNames: Record<keyof AccessibilitySettings, string> = {
      highContrast: 'High contrast mode',
      largeText: 'Large text mode',
      reducedMotion: 'Reduced motion mode',
      focusVisible: 'Enhanced focus indicators',
      keyboardNavigation: 'Keyboard navigation mode',
      screenReaderOptimizations: 'Screen reader optimizations'
    };

    const settingName = settingNames[key];
    const status = value ? 'enabled' : 'disabled';
    announceToScreenReader(`${settingName} ${status}`, 'polite');
  };

  // Function to reset all settings to default
  const resetSettings = () => {
    setSettings(defaultSettings);
    announceToScreenReader('Accessibility settings reset to default', 'polite');
  };

  // Function to announce messages to screen readers
  const announceToScreenReader = (message: string, priority: 'polite' | 'assertive' = 'polite') => {
    if (liveRegionElement) {
      // Clear previous message
      liveRegionElement.textContent = '';
      liveRegionElement.setAttribute('aria-live', priority);
      
      // Set new message after a brief delay to ensure screen readers pick it up
      setTimeout(() => {
        if (liveRegionElement) {
          liveRegionElement.textContent = message;
        }
      }, 100);

      // Clear message after announcement
      setTimeout(() => {
        if (liveRegionElement) {
          liveRegionElement.textContent = '';
        }
      }, 5000);
    }
  };

  // Context value
  const contextValue: AccessibilityContextType = {
    settings,
    updateSetting,
    resetSettings,
    announceToScreenReader,
  };

  return (
    <AccessibilityContext.Provider value={contextValue}>
      {children}
    </AccessibilityContext.Provider>
  );
}

// Export default
export default AccessibilityProvider;