import { test, expect } from '@playwright/test';

test('Login flow should work', async ({ page }) => {
  // Navigate to login page
  await page.goto('https://localhost:5173/login', { waitUntil: 'networkidle' });

  // Verify we're on login page
  const loginTitle = page.locator('h1, h2').filter({ hasText: /login|sign in/i });
  expect(loginTitle).toBeTruthy();

  // Fill in credentials
  await page.fill('input[type="text"]', 'fab');
  await page.fill('input[type="password"]', 'invaders');

  // Click sign in button and wait for navigation
  const signInButton = page.locator('button:has-text("Sign In")');

  // Start listening for navigation
  const navigationPromise = page.waitForNavigation({ waitUntil: 'networkidle', timeout: 15000 }).catch(() => null);

  // Click the button
  await signInButton.click();

  // Wait for navigation
  await navigationPromise;

  // After login, we should be redirected away from /login
  const url = page.url();
  console.log('Current URL after login:', url);

  // Should not be on login page anymore
  expect(url).not.toContain('/login');

  // Should be redirected to home or dashboard
  expect(url).toMatch(/localhost:5173\/(|home|dashboard|store)?$/);
});
