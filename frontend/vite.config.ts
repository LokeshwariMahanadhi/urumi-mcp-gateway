import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// The admin API allows this exact address, so keep the port fixed.
export default defineConfig({
  plugins: [react()],
  server: { host: "127.0.0.1", port: 5173, strictPort: true },
});
