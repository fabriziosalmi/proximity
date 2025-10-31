import adapter from '@sveltejs/adapter-auto';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
				preprocess: vitePreprocess(),

				kit: {
				 adapter: adapter(),

				 experimental: {
					 tracing: {
						 server: true
						},

					 instrumentation: {
						 server: true
						}
					}
				}
};

export default config;
