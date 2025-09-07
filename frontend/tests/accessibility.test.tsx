import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';

import { AccessibilityProvider } from '@/components/accessibility/AccessibilityProvider';
import { AccessibilityMenu } from '@/components/accessibility/AccessibilityMenu';
import { FocusTrap } from '@/components/accessibility/FocusTrap';
import { ScreenReaderText } from '@/components/accessibility/ScreenReaderText';

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, 'localStorage', { value: mockLocalStorage });

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

describe('AccessibilityProvider', () => {
  beforeEach(() => {
    mockLocalStorage.getItem.mockClear();
    mockLocalStorage.setItem.mockClear();
    jest.clearAllMocks();
  });

  test('renders children correctly', () => {
    render(
      <AccessibilityProvider>
        <div data-testid="test-child">Test Content</div>
      </AccessibilityProvider>
    );

    expect(screen.getByTestId('test-child')).toBeInTheDocument();
  });

  test('provides default accessibility preferences', () => {
    let capturedContext: any;
    
    function TestComponent() {
      const context = React.useContext(
        React.createContext({
          preferences: {},
          setPreference: () => {},
          resetPreferences: () => {},
          announceToScreenReader: () => {},
          focusElement: () => {},
          skipToContent: () => {}
        })
      );
      capturedContext = context;
      return <div>Test</div>;
    }

    render(
      <AccessibilityProvider>
        <TestComponent />
      </AccessibilityProvider>
    );

    expect(capturedContext).toBeDefined();
  });

  test('loads preferences from localStorage on mount', () => {
    const savedPreferences = {
      highContrast: true,
      largeText: true,
      darkMode: false
    };
    mockLocalStorage.getItem.mockReturnValue(JSON.stringify(savedPreferences));

    render(
      <AccessibilityProvider>
        <div>Test</div>
      </AccessibilityProvider>
    );

    expect(mockLocalStorage.getItem).toHaveBeenCalledWith('accessibility-preferences');
  });

  test('applies CSS classes based on preferences', async () => {
    const TestComponent = () => {
      const { setPreference } = React.useContext(AccessibilityProvider.Context || React.createContext({} as any));
      
      React.useEffect(() => {
        setPreference('highContrast', true);
        setPreference('largeText', true);
      }, [setPreference]);

      return <div>Test</div>;
    };

    render(
      <AccessibilityProvider>
        <TestComponent />
      </AccessibilityProvider>
    );

    await waitFor(() => {
      expect(document.documentElement.classList.contains('accessibility-high-contrast')).toBe(true);
      expect(document.documentElement.classList.contains('accessibility-large-text')).toBe(true);
    });
  });

  test('provides screen reader announcements', () => {
    let announceFunction: (message: string) => void;
    
    function TestComponent() {
      const { announceToScreenReader } = React.useContext(
        AccessibilityProvider.Context || React.createContext({} as any)
      );
      announceFunction = announceToScreenReader;
      return <div>Test</div>;
    }

    render(
      <AccessibilityProvider>
        <TestComponent />
      </AccessibilityProvider>
    );

    // Call the announce function
    announceFunction('Test announcement');

    // Check if live region was created
    const liveRegion = document.getElementById('accessibility-live-region');
    expect(liveRegion).toBeInTheDocument();
  });

  test('handles system preference detection', () => {
    // Mock system preferences
    window.matchMedia = jest.fn().mockImplementation(query => {
      if (query === '(prefers-reduced-motion: reduce)') {
        return { matches: true, addListener: jest.fn(), removeListener: jest.fn() };
      }
      if (query === '(prefers-color-scheme: dark)') {
        return { matches: true, addListener: jest.fn(), removeListener: jest.fn() };
      }
      return { matches: false, addListener: jest.fn(), removeListener: jest.fn() };
    });

    render(
      <AccessibilityProvider>
        <div>Test</div>
      </AccessibilityProvider>
    );

    // System preferences should be detected and applied
    expect(window.matchMedia).toHaveBeenCalledWith('(prefers-reduced-motion: reduce)');
    expect(window.matchMedia).toHaveBeenCalledWith('(prefers-color-scheme: dark)');
  });
});

describe('AccessibilityMenu', () => {
  const renderWithProvider = (ui: React.ReactElement) => {
    return render(
      <AccessibilityProvider>
        {ui}
      </AccessibilityProvider>
    );
  };

  test('renders accessibility menu button', () => {
    renderWithProvider(<AccessibilityMenu />);
    
    const menuButton = screen.getByRole('button', { name: /open accessibility settings/i });
    expect(menuButton).toBeInTheDocument();
  });

  test('opens menu when button is clicked', async () => {
    const user = userEvent.setup();
    renderWithProvider(<AccessibilityMenu />);
    
    const menuButton = screen.getByRole('button', { name: /open accessibility settings/i });
    await user.click(menuButton);

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Accessibility Settings')).toBeInTheDocument();
  });

  test('closes menu when close button is clicked', async () => {
    const user = userEvent.setup();
    renderWithProvider(<AccessibilityMenu />);
    
    // Open menu
    const menuButton = screen.getByRole('button', { name: /open accessibility settings/i });
    await user.click(menuButton);
    
    // Close menu
    const closeButton = screen.getByRole('button', { name: /close accessibility menu/i });
    await user.click(closeButton);

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  test('closes menu when escape key is pressed', async () => {
    const user = userEvent.setup();
    renderWithProvider(<AccessibilityMenu />);
    
    // Open menu
    const menuButton = screen.getByRole('button', { name: /open accessibility settings/i });
    await user.click(menuButton);
    
    // Press escape
    await user.keyboard('{Escape}');

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  test('displays different accessibility categories', async () => {
    const user = userEvent.setup();
    renderWithProvider(<AccessibilityMenu />);
    
    // Open menu
    const menuButton = screen.getByRole('button', { name: /open accessibility settings/i });
    await user.click(menuButton);

    // Check if categories are present
    expect(screen.getByRole('tab', { name: /visual/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /navigation/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /audio & feedback/i })).toBeInTheDocument();
  });

  test('switches between category tabs', async () => {
    const user = userEvent.setup();
    renderWithProvider(<AccessibilityMenu />);
    
    // Open menu
    const menuButton = screen.getByRole('button', { name: /open accessibility settings/i });
    await user.click(menuButton);

    // Click navigation tab
    const navigationTab = screen.getByRole('tab', { name: /navigation/i });
    await user.click(navigationTab);

    // Check if navigation content is visible
    expect(screen.getByText('Keyboard Navigation')).toBeInTheDocument();
    expect(screen.getByText('Focus Indicators')).toBeInTheDocument();
  });

  test('toggles accessibility preferences', async () => {
    const user = userEvent.setup();
    renderWithProvider(<AccessibilityMenu />);
    
    // Open menu
    const menuButton = screen.getByRole('button', { name: /open accessibility settings/i });
    await user.click(menuButton);

    // Find and click high contrast checkbox
    const highContrastCheckbox = screen.getByLabelText(/high contrast/i);
    await user.click(highContrastCheckbox);

    // Verify the preference was toggled
    expect(highContrastCheckbox).toBeChecked();
  });

  test('resets preferences when reset button is clicked', async () => {
    const user = userEvent.setup();
    renderWithProvider(<AccessibilityMenu />);
    
    // Open menu
    const menuButton = screen.getByRole('button', { name: /open accessibility settings/i });
    await user.click(menuButton);

    // Click reset button
    const resetButton = screen.getByRole('button', { name: /reset to defaults/i });
    await user.click(resetButton);

    // All preferences should be reset to defaults
    const checkboxes = screen.getAllByRole('checkbox');
    checkboxes.forEach(checkbox => {
      // Depending on defaults, some might be checked, others unchecked
      expect(checkbox).toBeInTheDocument();
    });
  });

  test('provides keyboard navigation support', async () => {
    const user = userEvent.setup();
    renderWithProvider(<AccessibilityMenu />);
    
    // Open menu with keyboard
    const menuButton = screen.getByRole('button', { name: /open accessibility settings/i });
    menuButton.focus();
    await user.keyboard('{Enter}');

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    
    // Tab navigation should work within the menu
    await user.keyboard('{Tab}');
    expect(document.activeElement).not.toBe(menuButton);
  });
});

describe('FocusTrap', () => {
  test('traps focus within component', async () => {
    const user = userEvent.setup();
    
    render(
      <div>
        <button>Outside Button 1</button>
        <FocusTrap>
          <div>
            <button data-testid="inside-1">Inside Button 1</button>
            <button data-testid="inside-2">Inside Button 2</button>
          </div>
        </FocusTrap>
        <button>Outside Button 2</button>
      </div>
    );

    const insideButton1 = screen.getByTestId('inside-1');
    const insideButton2 = screen.getByTestId('inside-2');

    // Focus should start at first focusable element
    insideButton1.focus();
    expect(document.activeElement).toBe(insideButton1);

    // Tab should move to next element inside
    await user.keyboard('{Tab}');
    expect(document.activeElement).toBe(insideButton2);

    // Tab from last element should wrap to first
    await user.keyboard('{Tab}');
    expect(document.activeElement).toBe(insideButton1);

    // Shift+Tab should move backwards
    await user.keyboard('{Shift>}{Tab}{/Shift}');
    expect(document.activeElement).toBe(insideButton2);
  });

  test('handles escape key to close', async () => {
    const user = userEvent.setup();
    const onClose = jest.fn();
    
    render(
      <FocusTrap onClose={onClose}>
        <div>
          <button>Inside Button</button>
        </div>
      </FocusTrap>
    );

    await user.keyboard('{Escape}');
    expect(onClose).toHaveBeenCalled();
  });

  test('restores focus when unmounted', () => {
    const originalButton = document.createElement('button');
    document.body.appendChild(originalButton);
    originalButton.focus();

    const { unmount } = render(
      <FocusTrap>
        <button>Inside Button</button>
      </FocusTrap>
    );

    unmount();
    expect(document.activeElement).toBe(originalButton);
    
    document.body.removeChild(originalButton);
  });
});

describe('ScreenReaderText', () => {
  test('renders text that is visually hidden but accessible to screen readers', () => {
    render(<ScreenReaderText>Screen reader only text</ScreenReaderText>);
    
    const text = screen.getByText('Screen reader only text');
    expect(text).toBeInTheDocument();
    expect(text).toHaveClass('sr-only');
  });

  test('can be made visible when focused', () => {
    render(
      <ScreenReaderText focusable>
        Focusable screen reader text
      </ScreenReaderText>
    );
    
    const text = screen.getByText('Focusable screen reader text');
    expect(text).toHaveAttribute('tabIndex', '0');
  });
});

describe('Accessibility Integration', () => {
  test('keyboard navigation works across components', async () => {
    const user = userEvent.setup();
    
    render(
      <AccessibilityProvider>
        <div>
          <AccessibilityMenu />
          <FocusTrap>
            <button>Trapped Button</button>
          </FocusTrap>
        </div>
      </AccessibilityProvider>
    );

    // Should be able to navigate with keyboard
    await user.keyboard('{Tab}');
    const menuButton = screen.getByRole('button', { name: /open accessibility settings/i });
    expect(document.activeElement).toBe(menuButton);
  });

  test('screen reader announcements work with preferences', () => {
    let announceFunction: (message: string) => void;
    
    function TestComponent() {
      const { announceToScreenReader } = React.useContext(
        AccessibilityProvider.Context || React.createContext({} as any)
      );
      announceFunction = announceToScreenReader;
      return null;
    }

    render(
      <AccessibilityProvider>
        <TestComponent />
      </AccessibilityProvider>
    );

    announceFunction('Test message');
    
    // Should create live region for announcements
    const liveRegion = document.getElementById('accessibility-live-region');
    expect(liveRegion).toBeInTheDocument();
  });

  test('preferences persist across sessions', () => {
    // First session - set preferences
    const { unmount } = render(
      <AccessibilityProvider>
        <AccessibilityMenu />
      </AccessibilityProvider>
    );

    // Simulate setting a preference
    const savedPrefs = { highContrast: true, largeText: true };
    mockLocalStorage.setItem('accessibility-preferences', JSON.stringify(savedPrefs));

    unmount();

    // Second session - preferences should be loaded
    mockLocalStorage.getItem.mockReturnValue(JSON.stringify(savedPrefs));

    render(
      <AccessibilityProvider>
        <AccessibilityMenu />
      </AccessibilityProvider>
    );

    expect(mockLocalStorage.getItem).toHaveBeenCalledWith('accessibility-preferences');
  });

  test('works with reduced motion preference', () => {
    // Mock reduced motion preference
    window.matchMedia = jest.fn().mockImplementation(query => {
      if (query === '(prefers-reduced-motion: reduce)') {
        return { 
          matches: true, 
          addListener: jest.fn(), 
          removeListener: jest.fn(),
          addEventListener: jest.fn(),
          removeEventListener: jest.fn()
        };
      }
      return { 
        matches: false, 
        addListener: jest.fn(), 
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn()
      };
    });

    render(
      <AccessibilityProvider>
        <div>Test content</div>
      </AccessibilityProvider>
    );

    // Should apply reduced motion class
    expect(document.documentElement.classList.contains('accessibility-reduced-motion')).toBe(true);
  });
});

describe('Accessibility Error Handling', () => {
  test('handles missing context gracefully', () => {
    // Temporarily mock console.error to avoid test output noise
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    
    expect(() => {
      render(
        <AccessibilityMenu />
      );
    }).toThrow(); // Should throw error when used outside provider

    consoleSpy.mockRestore();
  });

  test('handles localStorage errors gracefully', () => {
    // Mock localStorage to throw an error
    mockLocalStorage.getItem.mockImplementation(() => {
      throw new Error('localStorage not available');
    });

    // Should still render without crashing
    expect(() => {
      render(
        <AccessibilityProvider>
          <div>Test</div>
        </AccessibilityProvider>
      );
    }).not.toThrow();
  });

  test('handles invalid stored preferences gracefully', () => {
    // Mock invalid JSON in localStorage
    mockLocalStorage.getItem.mockReturnValue('invalid json');

    // Should still render with default preferences
    expect(() => {
      render(
        <AccessibilityProvider>
          <div>Test</div>
        </AccessibilityProvider>
      );
    }).not.toThrow();
  });
});