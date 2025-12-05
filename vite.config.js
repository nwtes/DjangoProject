import { defineConfig } from "vite";

export default defineConfig({
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
