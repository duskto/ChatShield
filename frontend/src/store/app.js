import { defineStore } from "pinia";

import { fetchModerationStatus, fetchOllamaStatus, fetchSystemConfig } from "../api/config";

export const useAppStore = defineStore("app", {
  state: () => ({
    title: import.meta.env.VITE_APP_TITLE || "ChatShield",
    config: null,
    ollamaStatus: null,
    moderationStatus: null,
    loading: false,
  }),
  actions: {
    async hydrate() {
      this.loading = true;
      try {
        const [config, ollamaStatus, moderationStatus] = await Promise.all([
          fetchSystemConfig(),
          fetchOllamaStatus(),
          fetchModerationStatus(),
        ]);
        this.config = config;
        this.ollamaStatus = ollamaStatus;
        this.moderationStatus = moderationStatus;
      } finally {
        this.loading = false;
      }
    },
  },
});

