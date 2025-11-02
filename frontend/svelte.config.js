import adapter from '@sveltejs/adapter-node';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	kit: {
		// Use adapter-node for production deployment
		adapter: adapter(),

		// Proxy API calls to FastAPI backend
		alias: {
			$lib: 'src/lib'
		}
	}
};

export default config;
