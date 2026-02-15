import { defineConfig } from "vite";

export default defineConfig({
  base: "/static/",
  publicDir: false,
  build: {
    manifest: true,
    outDir: "static_build",
    emptyOutDir: true,
    rollupOptions: {
      input: {
        "js/editor.js": "static/js/editor.js"
      }
    }
  }
});
