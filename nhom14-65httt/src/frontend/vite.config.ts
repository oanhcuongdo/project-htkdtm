import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// https://vite.dev/config/
export default defineConfig(({ mode }) => ({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/health": {
        target:
          loadEnv(mode, process.cwd(), "").API_PROXY_TARGET ||
          "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/api": {
        target:
          loadEnv(mode, process.cwd(), "").API_PROXY_TARGET ||
          "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
}));
