/**
 * SvelteKit Client Hooks
 * Runs in the browser
 */

import { handleErrorWithSentry, replayIntegration } from '@sentry/sveltekit';
import * as Sentry from '@sentry/sveltekit';

Sentry.init({
	dsn: import.meta.env.VITE_SENTRY_DSN || 'https://dbee00d4782d131ab54ffe60b16d969b@o149725.ingest.us.sentry.io/4510189390266368',
	environment: import.meta.env.VITE_SENTRY_ENVIRONMENT || import.meta.env.MODE || 'development',
	tracesSampleRate: parseFloat(import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE || '1.0'),

	// This sets the sample rate to be 100% in development, adjust for production
	replaysSessionSampleRate: 0.1,

	// If the entire session is not sampled, use the below sample rate to sample
	// sessions when an error occurs.
	replaysOnErrorSampleRate: 1.0,

	// If you don't want to use Session Replay, just remove the line below:
	integrations: [replayIntegration()],

	// Don't send errors in development mode unless explicitly enabled
	beforeSend(event) {
		if (import.meta.env.DEV && import.meta.env.VITE_SENTRY_DEBUG !== 'true') {
			console.log('🔴 [Sentry Client] Error captured (not sent in dev):', event);
			return null;
		}
		return event;
	}
});

// If you have a custom error handler, pass it to `handleErrorWithSentry`
export const handleError = handleErrorWithSentry();
