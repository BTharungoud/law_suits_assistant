import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Polyfill for globalThis.crypto.getRandomValues for older Node versions (e.g. Node 16)
// Vite may expect `crypto.getRandomValues` during config resolution. If Node's
// WebCrypto API is unavailable, provide a minimal polyfill using Node's
// `crypto.randomFillSync` so the dev server can start.
import { randomFillSync } from 'crypto';
if (typeof globalThis.crypto === 'undefined' || typeof globalThis.crypto.getRandomValues !== 'function') {
    globalThis.crypto = {
        getRandomValues: (arr) => {
            if (!(arr instanceof Uint8Array)) throw new TypeError('Expected Uint8Array');
            return randomFillSync(arr);
        }
    };
}
export default defineConfig({
    plugins: [react()],
    server: {
        port: 3000,
        proxy: {
            '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true,
            }
        }
    }
});
