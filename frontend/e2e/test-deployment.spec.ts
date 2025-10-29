import { test, expect } from '@playwright/test';

test('Test deployment hostname change', async ({ page, context }) => {
  // Ignore SSL certificate errors for HTTPS testing
  context.clearCookies();

  // Login
  await page.goto('https://localhost:5173/login', { waitUntil: 'networkidle' });
  await page.fill('input#username', 'fab');
  await page.fill('input#password', 'invaders');
  await page.click('button:has-text("Sign In")');

  // Wait for navigation to complete
  await page.waitForURL('https://localhost:5173/');

  // Go to Store
  await page.goto('https://localhost:5173/store');
  await page.waitForLoadState('networkidle');

  // Click Deploy button
  console.log('🚀 Clicking Deploy button...');
  await page.click('button:has-text("🚀 Deploy")');

  // Wait for modal to open
  await page.waitForSelector('[role="dialog"]', { timeout: 5000 });
  console.log('✅ Modal opened');

  // Wait a bit for the form to load
  await page.waitForTimeout(1000);

  // Check if hostname input exists and is enabled
  const hostnameInput = page.locator('#hostname');
  const isDisabled = await hostnameInput.isDisabled();
  console.log('🔍 Hostname input disabled?', isDisabled);

  const currentValue = await hostnameInput.inputValue();
  console.log('📝 Current hostname value:', currentValue);

  // Try to clear and type new value
  console.log('🖊️  Attempting to change hostname...');
  await hostnameInput.click();
  await hostnameInput.fill('');
  await hostnameInput.fill('test-hostname-999');

  const newValue = await hostnameInput.inputValue();
  console.log('✅ New hostname value:', newValue);

  // Listen for console logs
  page.on('console', msg => {
    if (msg.text().includes('🔴') || msg.text().includes('🎯') || msg.text().includes('⚡') ||
        msg.text().includes('💾') || msg.text().includes('🚀') || msg.text().includes('Hostname')) {
      console.log('Browser log:', msg.text());
    }
  });

  // Click Deploy button in modal
  console.log('🎯 Clicking Deploy in modal...');
  await page.click('button:has-text("Deploy")');

  // Wait a bit to see logs
  await page.waitForTimeout(3000);

  console.log('✅ Test completed');
});
