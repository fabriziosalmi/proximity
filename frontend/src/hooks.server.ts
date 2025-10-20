/**
 * SvelteKit Server Hooks
 * Runs on the server (during SSR)
 */

import * as Sentry from '@sentry/sveltekit';
import { handleErrorWithSentry } from '@sentry/sveltekit';

Sentry.init({
	dsn: import.meta.env.VITE_SENTRY_DSN || 'https://dbee00d4782d131ab54ffe60b16d969b@o149725.ingest.us.sentry.io/4510189390266368',
	environment: import.meta.env.VITE_SENTRY_ENVIRONMENT || import.meta.env.MODE || 'development',
	tracesSampleRate: parseFloat(import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE || '1.0'),
	
	// Enable logs to be sent to Sentry
	enableLogs: true,

	// Don't send errors in development mode unless explicitly enabled
	beforeSend(event) {
		if (import.meta.env.DEV && import.meta.env.VITE_SENTRY_DEBUG !== 'true') {
			console.log('🔴 [Sentry Server] Error captured (not sent in dev):', event);
			return null;
		}
		return event;
	}
});

export const handleError = handleErrorWithSentry();
