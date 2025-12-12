import { defineConfig } from "vite";

export default defineConfig({
  base: "/static/assets/",
  publicDir: false,   // optional but recommended
  server: {
    host: true,
    port: 5173,
    cors: true,
    headers: {
      "Access-Control-Allow-Origin": "*"
    }
  },
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
