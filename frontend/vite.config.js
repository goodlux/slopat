import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		// Proxy API requests to FastAPI backend
		proxy: {
			'/api': {
				target: 'http://localhost:8001',
				changeOrigin: true
			}
		}
	}
});
