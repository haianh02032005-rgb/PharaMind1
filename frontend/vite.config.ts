import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  assetsInclude: ["**/*.glb"],
  server: {
    port: 5173,
    host: true,
    proxy: {
      "/auth": "http://127.0.0.1:8000",
      "/users": "http://127.0.0.1:8000",
      "/families": "http://127.0.0.1:8000",
      "/imports": "http://127.0.0.1:8000",
      "/health": "http://127.0.0.1:8000",
      "/ws": {
        target: "ws://127.0.0.1:8000",
        ws: true,
      },
    },
  },
});

