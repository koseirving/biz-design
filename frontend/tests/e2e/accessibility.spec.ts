import { test, expect } from '@playwright/test';

test.describe('Accessibility E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the app
    await page.goto('/');
  });

  test('accessibility menu can be opened and closed', async ({ page }) => {
    // Look for accessibility menu button
    const menuButton = page.getByRole('button', { name: /accessibility settings/i });
    await expect(menuButton).toBeVisible();

    // Open the menu
    await menuButton.click();

    // Check if menu dialog is visible
    const menuDialog = page.getByRole('dialog');
    await expect(menuDialog).toBeVisible();
    await expect(page.getByText('Accessibility Settings')).toBeVisible();

    // Close the menu using close button
    const closeButton = page.getByRole('button', { name: /close/i });
    await closeButton.click();

    // Menu should be closed
    await expect(menuDialog).not.toBeVisible();
  });

  test('accessibility menu can be closed with escape key', async ({ page }) => {
    // Open accessibility menu
    const menuButton = page.getByRole('button', { name: /accessibility settings/i });
    await menuButton.click();

    const menuDialog = page.getByRole('dialog');
    await expect(menuDialog).toBeVisible();

    // Press escape key
    await page.keyboard.press('Escape');

    // Menu should be closed
    await expect(menuDialog).not.toBeVisible();
  });

  test('can switch between accessibility categories', async ({ page }) => {
    // Open accessibility menu
    const menuButton = page.getByRole('button', { name: /accessibility settings/i });
    await menuButton.click();

    // Check default tab (Visual)
    const visualTab = page.getByRole('tab', { name: /visual/i });
    await expect(visualTab).toHaveAttribute('aria-selected', 'true');
    await expect(page.getByText('High Contrast')).toBeVisible();

    // Switch to Navigation tab
    const navigationTab = page.getByRole('tab', { name: /navigation/i });
    await navigationTab.click();
    await expect(navigationTab).toHaveAttribute('aria-selected', 'true');
    await expect(page.getByText('Keyboard Navigation')).toBeVisible();

    // Switch to Audio & Feedback tab
    const audioTab = page.getByRole('tab', { name: /audio.*feedback/i });
    await audioTab.click();
    await expect(audioTab).toHaveAttribute('aria-selected', 'true');
    await expect(page.getByText('Sound Effects')).toBeVisible();
  });

  test('can toggle accessibility preferences', async ({ page }) => {
    // Open accessibility menu
    const menuButton = page.getByRole('button', { name: /accessibility settings/i });
    await menuButton.click();

    // Find high contrast checkbox
    const highContrastCheckbox = page.getByRole('checkbox', { name: /high contrast/i });
    
    // Toggle the preference
    const isInitiallyChecked = await highContrastCheckbox.isChecked();
    await highContrastCheckbox.click();
    
    // Verify the state changed
    const isNowChecked = await highContrastCheckbox.isChecked();
    expect(isNowChecked).toBe(!isInitiallyChecked);

    // Check if CSS class is applied to document
    if (isNowChecked) {
      await expect(page.locator('html')).toHaveClass(/accessibility-high-contrast/);
    } else {
      await expect(page.locator('html')).not.toHaveClass(/accessibility-high-contrast/);
    }
  });

  test('can reset accessibility preferences', async ({ page }) => {
    // Open accessibility menu
    const menuButton = page.getByRole('button', { name: /accessibility settings/i });
    await menuButton.click();

    // Toggle some preferences first
    await page.getByRole('checkbox', { name: /high contrast/i }).click();
    await page.getByRole('checkbox', { name: /large text/i }).click();

    // Click reset button
    const resetButton = page.getByRole('button', { name: /reset to defaults/i });
    await resetButton.click();

    // Preferences should be reset to defaults
    // (Assuming defaults are false for these preferences)
    await expect(page.getByRole('checkbox', { name: /high contrast/i })).not.toBeChecked();
    await expect(page.getByRole('checkbox', { name: /large text/i })).not.toBeChecked();

    // CSS classes should be removed
    await expect(page.locator('html')).not.toHaveClass(/accessibility-high-contrast/);
    await expect(page.locator('html')).not.toHaveClass(/accessibility-large-text/);
  });

  test('keyboard navigation works in accessibility menu', async ({ page }) => {
    // Navigate to accessibility button using keyboard
    await page.keyboard.press('Tab');
    // Continue tabbing until we reach the accessibility button
    // (This assumes the accessibility button is focusable via tab navigation)
    
    const menuButton = page.getByRole('button', { name: /accessibility settings/i });
    await menuButton.focus();
    
    // Open menu with keyboard
    await page.keyboard.press('Enter');
    
    const menuDialog = page.getByRole('dialog');
    await expect(menuDialog).toBeVisible();

    // Tab navigation should work within the menu
    await page.keyboard.press('Tab');
    
    // Should be able to navigate to tabs
    await page.keyboard.press('ArrowRight');
    const navigationTab = page.getByRole('tab', { name: /navigation/i });
    await expect(navigationTab).toBeFocused();

    // Should be able to activate tab with Enter
    await page.keyboard.press('Enter');
    await expect(navigationTab).toHaveAttribute('aria-selected', 'true');
  });

  test('focus trap works in accessibility menu', async ({ page }) => {
    // Add a button before and after the menu for testing focus trap
    await page.evaluate(() => {
      const beforeButton = document.createElement('button');
      beforeButton.textContent = 'Before Button';
      beforeButton.id = 'before-button';
      document.body.insertBefore(beforeButton, document.body.firstChild);

      const afterButton = document.createElement('button');
      afterButton.textContent = 'After Button';
      afterButton.id = 'after-button';
      document.body.appendChild(afterButton);
    });

    // Open accessibility menu
    const menuButton = page.getByRole('button', { name: /accessibility settings/i });
    await menuButton.click();

    // Focus should be trapped within the menu
    // Tab through all elements in the menu and verify focus doesn't escape
    const elementsInMenu = await page.locator('[role="dialog"] [tabindex]:not([tabindex="-1"]), [role="dialog"] button, [role="dialog"] input, [role="dialog"] [role="tab"]').count();
    
    for (let i = 0; i < elementsInMenu + 2; i++) {
      await page.keyboard.press('Tab');
    }

    // Focus should still be within the dialog
    const focusedElement = page.locator(':focus');
    const dialogElement = page.getByRole('dialog');
    await expect(dialogElement).toContainText(await focusedElement.textContent() || '');
  });

  test('screen reader announcements work', async ({ page }) => {
    // Open accessibility menu
    const menuButton = page.getByRole('button', { name: /accessibility settings/i });
    await menuButton.click();

    // Check if live region exists
    const liveRegion = page.locator('#accessibility-live-region');
    await expect(liveRegion).toBeAttached();
    await expect(liveRegion).toHaveAttribute('aria-live', 'polite');

    // Toggle a preference to trigger an announcement
    await page.getByRole('checkbox', { name: /high contrast/i }).click();

    // The live region should eventually contain an announcement
    await expect(liveRegion).toContainText(/contrast/, { timeout: 5000 });
  });

  test('skip links are present and functional', async ({ page }) => {
    // Skip links should be present but hidden
    const skipLink = page.getByRole('button', { name: /skip to main content/i });
    await expect(skipLink).toBeAttached();

    // Focus the skip link (it should become visible when focused)
    await skipLink.focus();
    
    // Click the skip link
    await skipLink.click();

    // Should focus main content area
    const mainContent = page.locator('main, #main-content, [role="main"]').first();
    if (await mainContent.count() > 0) {
      await expect(mainContent).toBeFocused();
    }
  });

  test('large text preference affects text size', async ({ page }) => {
    // Open accessibility menu
    const menuButton = page.getByRole('button', { name: /accessibility settings/i });
    await menuButton.click();

    // Get initial text size of a sample element
    const sampleText = page.getByText('Accessibility Settings').first();
    const initialSize = await sampleText.evaluate(el => getComputedStyle(el).fontSize);

    // Toggle large text preference
    await page.getByRole('checkbox', { name: /large text/i }).click();

    // Text size should increase
    const newSize = await sampleText.evaluate(el => getComputedStyle(el).fontSize);
    
    // Convert to numbers for comparison (removing 'px')
    const initialSizeNum = parseFloat(initialSize);
    const newSizeNum = parseFloat(newSize);
    
    expect(newSizeNum).toBeGreaterThan(initialSizeNum);
  });

  test('reduced motion preference affects animations', async ({ page }) => {
    // Open accessibility menu
    const menuButton = page.getByRole('button', { name: /accessibility settings/i });
    await menuButton.click();

    // Toggle reduced motion preference
    await page.getByRole('checkbox', { name: /reduced motion/i }).click();

    // Check if CSS class is applied
    await expect(page.locator('html')).toHaveClass(/accessibility-reduced-motion/);

    // Close menu with animation - should be reduced/instant
    await page.keyboard.press('Escape');
    
    // Menu should close immediately or with minimal animation
    const menuDialog = page.getByRole('dialog');
    await expect(menuDialog).not.toBeVisible();
  });

  test('accessibility preferences persist across page reloads', async ({ page }) => {
    // Open accessibility menu and set preferences
    const menuButton = page.getByRole('button', { name: /accessibility settings/i });
    await menuButton.click();
    
    await page.getByRole('checkbox', { name: /high contrast/i }).click();
    await page.getByRole('checkbox', { name: /large text/i }).click();
    
    // Close menu
    await page.keyboard.press('Escape');

    // Reload page
    await page.reload();

    // Preferences should be maintained
    await expect(page.locator('html')).toHaveClass(/accessibility-high-contrast/);
    await expect(page.locator('html')).toHaveClass(/accessibility-large-text/);

    // Open menu again to verify checkboxes are still checked
    await menuButton.click();
    await expect(page.getByRole('checkbox', { name: /high contrast/i })).toBeChecked();
    await expect(page.getByRole('checkbox', { name: /large text/i })).toBeChecked();
  });
});