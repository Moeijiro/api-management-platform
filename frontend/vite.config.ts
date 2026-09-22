import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "node:path";

// The dashboard talks to /api and /auth; /v1 is proxied too so the examples on
// the documentation page can be run straight from the browser. The keys are
// regexes so a client-side route that merely starts with the same letters is
// not swallowed by the proxy.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { "@": path.resolve(__dirname, "./src") } },
  server: {
    port: 5173,
    proxy: {
      "^/api/": { target: process.env.VITE_API_TARGET ?? "http://localhost:8000" },
      "^/auth/": { target: process.env.VITE_API_TARGET ?? "http://localhost:8000" },
      "^/v1/": { target: process.env.VITE_API_TARGET ?? "http://localhost:8000" },
    },
  },
});
