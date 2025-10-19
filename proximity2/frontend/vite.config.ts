import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vitest/config';
import { sentrySvelteKit } from '@sentry/sveltekit';

export default defineConfig({
	plugins: [
		sentrySvelteKit({
			sourceMapsUploadOptions: {
				org: 'proximity',
				project: 'proximity-2-frontend',
				authToken: process.env.SENTRY_AUTH_TOKEN,
			},
		}),
		sveltekit(),
	],
	test: {
		include: ['src/**/*.{test,spec}.{js,ts}']
	},
	server: {
		host: true,
		port: 5173
	}
});
