import { defineStore } from "pinia";

import {
  fetchConfigBootstrap,
} from "../api/config";

export const useAppStore = defineStore("app", {
  state: () => ({
    title: import.meta.env.VITE_APP_TITLE || "ChatShield",
    config: null,
    ollamaStatus: null,
    moderationStatus: null,
    models: [],
    defaultModel: "qwen2.5:3b",
    loading: false,
  }),
  actions: {
    async hydrate(forceRefresh = false) {
      this.loading = true;
      try {
        const bootstrap = await fetchConfigBootstrap(forceRefresh);
        this.config = bootstrap.config;
        this.ollamaStatus = bootstrap.ollama_status;
        this.moderationStatus = bootstrap.moderation_status;
        this.models = bootstrap.models.models?.length
          ? bootstrap.models.models
          : [bootstrap.models.default_model];
        this.defaultModel = bootstrap.models.default_model || "qwen2.5:3b";
      } finally {
        this.loading = false;
      }
    },
  },
});
