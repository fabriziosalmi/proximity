/**
 * SvelteKit Server Hooks
 * Runs on the server (during SSR)
 */

import * as Sentry from '@sentry/sveltekit';
import { handleErrorWithSentry } from '@sentry/sveltekit';

// 🔐 Security: Sentry DSN must be provided via environment variable
// Do not use fallback DSNs to prevent accidental error reporting to wrong account
const dsn = import.meta.env.VITE_SENTRY_DSN;
if (!dsn && import.meta.env.PROD) {
	console.error('⚠️ CRITICAL: VITE_SENTRY_DSN environment variable is required in production');
}

Sentry.init({
	dsn: dsn || undefined,
	environment: import.meta.env.VITE_SENTRY_ENVIRONMENT || import.meta.env.MODE || 'development',
	tracesSampleRate: parseFloat(import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE || '1.0'),

	// Enable logs to be sent to Sentry
	enableLogs: true,

	// Don't send errors in development mode unless explicitly enabled
	beforeSend(event) {
		if (import.meta.env.DEV && import.meta.env.VITE_SENTRY_DEBUG !== 'true') {
			return null; // Suppress errors in dev unless debug enabled
		}
		return event;
	}
});

export const handleError = handleErrorWithSentry();

/**
 * 🔐 Content Security Policy (CSP) Headers
 * Restricts resource loading to prevent XSS attacks
 */
export async function handle({ event, resolve }) {
	const response = await resolve(event);

	// Set CSP header to restrict resource loading
	response.headers.set(
		'Content-Security-Policy',
		// Development: More permissive to allow hot module reload
		// Production: Strict policies to prevent XSS
		import.meta.env.DEV
			? // Dev CSP: allows localhost for HMR
			  "default-src 'self' http://localhost:* https://localhost:* ws://localhost:* wss://localhost:*; " +
			  "script-src 'self' 'unsafe-inline' 'unsafe-eval' http://localhost:* https://localhost:*; " +
			  "worker-src 'self' blob:; " +
			  "style-src 'self' 'unsafe-inline' http://localhost:* https://localhost:*; " +
			  "img-src 'self' data: https:; " +
			  "font-src 'self' data:; " +
			  "connect-src 'self' http://localhost:* https://localhost:* ws://localhost:* wss://localhost:* https://*.sentry.io; " +
			  "frame-ancestors 'none'; " +
			  "base-uri 'self'; " +
			  "form-action 'self'"
			: // Production CSP: strict, only allows resources from same origin
			  "default-src 'self'; " +
			  "script-src 'self' https://*.sentry.io; " +
			  "worker-src 'self' blob:; " +
			  "style-src 'self'; " +
			  "img-src 'self' data: https:; " +
			  "font-src 'self' data:; " +
			  "connect-src 'self' https://*.sentry.io; " +
			  "frame-ancestors 'none'; " +
			  "base-uri 'self'; " +
			  "form-action 'self'"
	);

	// Additional security headers
	response.headers.set('X-Content-Type-Options', 'nosniff'); // Prevent MIME type sniffing
	response.headers.set('X-Frame-Options', 'DENY'); // Prevent clickjacking
	response.headers.set('X-XSS-Protection', '1; mode=block'); // Enable XSS protection
	response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin'); // Control referrer info

	return response;
}
