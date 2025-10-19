/**
 * SvelteKit Server Hooks
 * Runs on the server (during SSR)
 */

import * as Sentry from '@sentry/sveltekit';
import { handleErrorWithSentry } from '@sentry/sveltekit';

Sentry.init({
	dsn: 'https://dbee00d4782d131ab54ffe60b16d969b@o149725.ingest.us.sentry.io/4510189390266368',
	environment: import.meta.env.MODE || 'development',
	release: '2.0.0',
	tracesSampleRate: 0.1,

	// Don't send errors in development mode
	beforeSend(event) {
		if (import.meta.env.DEV) {
			console.log('🔴 [Sentry Server] Error captured (not sent in dev):', event);
			return null;
		}
		return event;
	}
});

export const handleError = handleErrorWithSentry();
