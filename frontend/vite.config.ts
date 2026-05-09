import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// envDir = ".." so Vite picks up the monorepo-root .env where
// VITE_BACKEND_WS_URL and VITE_BACKEND_HTTP_URL live.
export default defineConfig({
  plugins: [react()],
  envDir: "..",
  server: {
    port: 5173,
  },
});