import { defineConfig } from "vite";

export default defineConfig({
    server: {
        // Ensure dev server is reachable and allows cross-origin requests from Django
        host: true,
        port: 5173,
        strictPort: false,
        cors: true,
        // Provide permissive header for development (do not use this in production)
        headers: {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, PATCH, OPTIONS',
            'Access-Control-Allow-Headers': 'X-Requested-With, Content-Type, Authorization'
        },
        // HMR host settings (helpful if Django is served on another host/port)
        hmr: {
            host: 'localhost',
            port: 5173,
        }
    },
    build: {
        manifest: true,
        outDir: "static_build",
        emptyOutDir: true,
        rollupOptions: {
            input: {
                editor: "static/js/editor.js",
            },
        },
    },
});
