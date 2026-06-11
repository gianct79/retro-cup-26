import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
  plugins: [svelte()],
  base: '/retro-cup-26/',
  server: {
    port: 3000,
    open: true,
  },
});
