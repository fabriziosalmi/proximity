import { test, expect } from '@playwright/test';

test('Test deployment hostname change', async ({ page, context }) => {
  // Ignore SSL certificate errors for HTTPS testing
  context.clearCookies();

  // Capture all console messages for debugging
  page.on('console', msg => {
    const level = msg.type();
    const text = msg.text();
    if (level === 'error' || level === 'warning' || text.includes('Login') || text.includes('login') || text.includes('redirect')) {
      console.log(`[${level.toUpperCase()}] ${text}`);
    }
  });

  // Capture all network requests for debugging
  page.on('response', response => {
    if (response.url().includes('login') || response.url().includes('auth')) {
      console.log(`[${response.status()}] ${response.url()}`);
    }
  });

  // Login
  await page.goto('https://localhost:5173/login', { waitUntil: 'networkidle' });
  console.log('✅ Login page loaded');

  await page.fill('input#username', 'fab');
  await page.fill('input#password', 'invaders');
  console.log('✅ Credentials filled');

  // Click Sign In button and wait for API response
  const signInButton = page.locator('button:has-text("Sign In")');
  console.log('🔍 Sign In button found, clicking...');

  // Wait for the login API call to complete and navigation
  let navigationCompleted = false;
  let navigationError: Error | null = null;

  page.waitForNavigation({ timeout: 10000 })
    .then(() => {
      navigationCompleted = true;
      console.log('✅ Navigation completed successfully');
    })
    .catch(err => {
      navigationError = err;
      console.log('ℹ️ Navigation did not occur (may have already been on home page)');
    });

  // Add small delay to let navigation listener attach
  await page.waitForTimeout(100);

  // Click the button
  await signInButton.click();
  console.log('✅ Sign In button clicked');

  // Wait a bit longer for potential redirect or API processing
  await page.waitForTimeout(3000);

  // Check current URL
  const currentUrl = page.url();
  console.log('📍 Current URL:', currentUrl);

  // If still on login page, check for errors
  if (currentUrl.includes('/login')) {
    console.log('⚠️ Still on login page, checking for errors...');

    // Check for error messages
    const errorElement = page.locator('[role="alert"], .error, .text-red-600, .text-red-500');
    const errorCount = await errorElement.count();
    if (errorCount > 0) {
      const errorText = await errorElement.first().textContent();
      console.log('❌ Error message found:', errorText);
    }

    // Try to check auth store state via page evaluation
    try {
      const authStoreInfo = await page.evaluate(() => {
        return (window as any).authStore?.state || 'AuthStore not available';
      });
      console.log('🔐 Auth store state:', authStoreInfo);
    } catch (e) {
      console.log('ℹ️ Could not access auth store state');
    }
  } else {
    console.log('✅ Successfully redirected from login page');
  }

  // Navigate to Store (whether login worked or not, to test store page)
  console.log('🚀 Navigating to /store...');
  try {
    await page.goto('https://localhost:5173/store', { waitUntil: 'networkidle', timeout: 15000 });
    console.log('✅ Store page loaded');
  } catch (e) {
    console.log('⚠️ Failed to load store page:', (e as Error).message);
    // Try going to home page instead
    await page.goto('https://localhost:5173/', { waitUntil: 'networkidle', timeout: 15000 });
    console.log('✅ Home page loaded');
  }

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
