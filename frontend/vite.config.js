import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  server: {
    host: "0.0.0.0",
    port: 5173,
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes("node_modules")) {
            return;
          }
          if (id.includes("/echarts/")) {
            return "echarts";
          }
          if (id.includes("/vue/") || id.includes("/vue-router/") || id.includes("/pinia/")) {
            return "vue-core";
          }
        },
      },
    },
  },
});
