/**
 * Sentry Configuration for Proximity Platform
 * 
 * This module initializes Sentry error tracking for the frontend.
 * It captures JavaScript errors, unhandled promise rejections, and provides
 * context about user sessions and application state.
 */

// Wait for Sentry SDK to load
window.addEventListener('load', () => {
    if (typeof Sentry === 'undefined') {
        console.warn('⚠️ Sentry SDK not loaded - error tracking disabled');
        return;
    }

    try {
        // Initialize Sentry
        Sentry.init({
            dsn: "https://dbee00d4782d131ab54ffe60b16d969b@o149725.ingest.us.sentry.io/4510189390266368",
            
            // Send default PII (IP addresses, user agent)
            sendDefaultPii: true,
            
            // Performance Monitoring
            integrations: [
                Sentry.browserTracingIntegration(),
                Sentry.replayIntegration({
                    maskAllText: true,
                    blockAllMedia: true,
                }),
            ],
            
            // Performance Monitoring - Sample Rate
            tracesSampleRate: 1.0, // Capture 100% of transactions for performance monitoring
            
            // Session Replay - Sample Rates
            replaysSessionSampleRate: 0.1, // 10% of regular sessions
            replaysOnErrorSampleRate: 1.0,  // 100% of sessions with errors
            
            // Environment
            environment: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
                ? 'development' 
                : 'production',
            
            // Release tracking
            release: 'proximity@0.1.0',
            
            // Ignore certain errors
            ignoreErrors: [
                // Browser extensions
                'top.GLOBALS',
                'chrome-extension://',
                'moz-extension://',
                // Random plugins/extensions
                'Can\'t find variable: ZiteReader',
                'jigsaw is not defined',
                'ComboSearch is not defined',
                // Network errors we can't control
                'NetworkError',
                'Network request failed',
                // ResizeObserver loop errors (browser quirk)
                'ResizeObserver loop limit exceeded',
                'ResizeObserver loop completed with undelivered notifications',
            ],
            
            // Only send errors from our domain
            allowUrls: [
                /https?:\/\/(.+\.)?proximity\./,
                /https?:\/\/localhost/,
                /https?:\/\/127\.0\.0\.1/,
            ],
            
            // Before sending to Sentry
            beforeSend(event, hint) {
                // Don't send events in development unless explicitly enabled
                if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
                    if (!localStorage.getItem('sentry_debug_enabled')) {
                        console.log('🔍 [Sentry Debug] Event blocked in development:', event);
                        return null;
                    }
                }
                
                // Add custom context
                event.contexts = event.contexts || {};
                event.contexts.app_state = {
                    current_view: document.querySelector('.view:not(.hidden)')?.id || 'unknown',
                    authenticated: !!localStorage.getItem('proximity_token'),
                    user_agent: navigator.userAgent,
                };
                
                return event;
            },
        });

        console.log('✅ Sentry initialized - Error tracking enabled');

        // Set user context when authenticated
        const setupSentryUser = () => {
            if (typeof Sentry === 'undefined' || typeof Sentry.setUser !== 'function') {
                console.warn('⚠️ Sentry.setUser not available');
                return;
            }
            
            const token = localStorage.getItem('proximity_token');
            if (token) {
                try {
                    const payload = JSON.parse(atob(token.split('.')[1]));
                    Sentry.setUser({
                        id: payload.user_id,
                        username: payload.sub,
                        role: payload.role,
                    });
                } catch (e) {
                    // Invalid token, ignore
                }
            } else {
                Sentry.setUser(null);
            }
        };

        // Setup user on page load
        setupSentryUser();

        // Update user context when localStorage changes
        window.addEventListener('storage', setupSentryUser);

        // Expose helper for manual error reporting
        window.reportToSentry = (error, context = {}) => {
            Sentry.captureException(error, {
                extra: context,
            });
        };

        // Add breadcrumb for navigation events
        window.addEventListener('hashchange', () => {
            Sentry.addBreadcrumb({
                category: 'navigation',
                message: `Navigated to ${window.location.hash || '/'}`,
                level: 'info',
            });
        });

    } catch (error) {
        console.error('❌ Failed to initialize Sentry:', error);
    }
});

/**
 * Helper function to capture custom events
 * Usage: captureAppEvent('deployment_failed', { app_name: 'wordpress', error: 'timeout' })
 */
window.captureAppEvent = (eventName, data = {}) => {
    if (typeof Sentry !== 'undefined') {
        Sentry.captureMessage(eventName, {
            level: 'info',
            extra: data,
        });
    }
};

/**
 * Helper to add breadcrumbs for debugging
 * Usage: addDebugBreadcrumb('User clicked deploy button', { app_id: 123 })
 */
window.addDebugBreadcrumb = (message, data = {}) => {
    if (typeof Sentry !== 'undefined') {
        Sentry.addBreadcrumb({
            category: 'user_action',
            message: message,
            data: data,
            level: 'info',
        });
    }
};

/**
 * Test Sentry Integration
 * This function triggers an intentional error to verify Sentry is working
 * Usage: window.testSentry()
 */
window.testSentry = () => {
    if (typeof Sentry === 'undefined') {
        console.error('❌ Sentry SDK not loaded - cannot test');
        return;
    }

    console.log('🧪 Testing Sentry integration...');
    console.log('📍 This will trigger an intentional error to verify Sentry captures it');
    console.log('🔍 Check your Sentry dashboard in ~30 seconds: https://proximity.sentry.io');
    
    // Add breadcrumb before error
    window.addDebugBreadcrumb('Sentry integration test triggered', {
        test_type: 'manual',
        timestamp: new Date().toISOString(),
    });

    // Trigger intentional error
    try {
        // This will throw: ReferenceError: myUndefinedFunction is not defined
        myUndefinedFunction();
    } catch (error) {
        // Report to Sentry with context
        window.reportToSentry(error, {
            context: 'sentry_integration_test',
            test_triggered: true,
            test_timestamp: new Date().toISOString(),
        });
        
        console.log('✅ Test error sent to Sentry successfully!');
        console.log('📊 Error details:', error.message);
        console.log('🔗 View in dashboard: https://proximity.sentry.io/issues/');
    }
};

// Log when Sentry config is fully loaded
console.log('📋 Sentry helpers loaded:');
console.log('   • window.reportToSentry(error, context)');
console.log('   • window.captureAppEvent(eventName, data)');
console.log('   • window.addDebugBreadcrumb(message, data)');
console.log('   • window.testSentry() - Test integration');
