import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vitest/config';
import { sentrySvelteKit } from '@sentry/sveltekit';
import * as fs from 'fs';
import * as path from 'path';

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
		port: 5173,
		https: {
			key: fs.readFileSync(path.resolve(__dirname, 'key.pem')),
			cert: fs.readFileSync(path.resolve(__dirname, 'cert.pem')),
		}
	}
});
