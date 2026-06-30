import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const apiBase = env.VITE_API_BASE_URL ?? "http://localhost:8000";

  return {
    plugins: [react()],
    server: {
      proxy: {
        "/auth": apiBase,
        "/products": apiBase,
        "/watchlist": apiBase,
        "/alerts": apiBase,
      },
    },
  };
});
