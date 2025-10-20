// vite.config.ts
import { sveltekit } from "file:///app/node_modules/@sveltejs/kit/src/exports/vite/index.js";
import { defineConfig } from "file:///app/node_modules/vitest/dist/config.js";
import { sentrySvelteKit } from "file:///app/node_modules/@sentry/sveltekit/build/esm/index.server.js";
var vite_config_default = defineConfig({
  plugins: [
    sentrySvelteKit({
      sourceMapsUploadOptions: {
        org: "proximity",
        project: "proximity-2-frontend",
        authToken: process.env.SENTRY_AUTH_TOKEN
      }
    }),
    sveltekit()
  ],
  test: {
    include: ["src/**/*.{test,spec}.{js,ts}"]
  },
  server: {
    host: true,
    port: 5173
  }
});
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcudHMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCIvYXBwXCI7Y29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2ZpbGVuYW1lID0gXCIvYXBwL3ZpdGUuY29uZmlnLnRzXCI7Y29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2ltcG9ydF9tZXRhX3VybCA9IFwiZmlsZTovLy9hcHAvdml0ZS5jb25maWcudHNcIjtpbXBvcnQgeyBzdmVsdGVraXQgfSBmcm9tICdAc3ZlbHRlanMva2l0L3ZpdGUnO1xuaW1wb3J0IHsgZGVmaW5lQ29uZmlnIH0gZnJvbSAndml0ZXN0L2NvbmZpZyc7XG5pbXBvcnQgeyBzZW50cnlTdmVsdGVLaXQgfSBmcm9tICdAc2VudHJ5L3N2ZWx0ZWtpdCc7XG5cbmV4cG9ydCBkZWZhdWx0IGRlZmluZUNvbmZpZyh7XG5cdHBsdWdpbnM6IFtcblx0XHRzZW50cnlTdmVsdGVLaXQoe1xuXHRcdFx0c291cmNlTWFwc1VwbG9hZE9wdGlvbnM6IHtcblx0XHRcdFx0b3JnOiAncHJveGltaXR5Jyxcblx0XHRcdFx0cHJvamVjdDogJ3Byb3hpbWl0eS0yLWZyb250ZW5kJyxcblx0XHRcdFx0YXV0aFRva2VuOiBwcm9jZXNzLmVudi5TRU5UUllfQVVUSF9UT0tFTixcblx0XHRcdH0sXG5cdFx0fSksXG5cdFx0c3ZlbHRla2l0KCksXG5cdF0sXG5cdHRlc3Q6IHtcblx0XHRpbmNsdWRlOiBbJ3NyYy8qKi8qLnt0ZXN0LHNwZWN9Lntqcyx0c30nXVxuXHR9LFxuXHRzZXJ2ZXI6IHtcblx0XHRob3N0OiB0cnVlLFxuXHRcdHBvcnQ6IDUxNzNcblx0fVxufSk7XG4iXSwKICAibWFwcGluZ3MiOiAiO0FBQThMLFNBQVMsaUJBQWlCO0FBQ3hOLFNBQVMsb0JBQW9CO0FBQzdCLFNBQVMsdUJBQXVCO0FBRWhDLElBQU8sc0JBQVEsYUFBYTtBQUFBLEVBQzNCLFNBQVM7QUFBQSxJQUNSLGdCQUFnQjtBQUFBLE1BQ2YseUJBQXlCO0FBQUEsUUFDeEIsS0FBSztBQUFBLFFBQ0wsU0FBUztBQUFBLFFBQ1QsV0FBVyxRQUFRLElBQUk7QUFBQSxNQUN4QjtBQUFBLElBQ0QsQ0FBQztBQUFBLElBQ0QsVUFBVTtBQUFBLEVBQ1g7QUFBQSxFQUNBLE1BQU07QUFBQSxJQUNMLFNBQVMsQ0FBQyw4QkFBOEI7QUFBQSxFQUN6QztBQUFBLEVBQ0EsUUFBUTtBQUFBLElBQ1AsTUFBTTtBQUFBLElBQ04sTUFBTTtBQUFBLEVBQ1A7QUFDRCxDQUFDOyIsCiAgIm5hbWVzIjogW10KfQo=
