import { defineStore } from "pinia";

import {
  fetchModerationStatus,
  fetchOllamaModels,
  fetchOllamaStatus,
  fetchSystemConfig,
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
    async hydrate() {
      this.loading = true;
      try {
        const [config, ollamaStatus, moderationStatus, modelInfo] = await Promise.all([
          fetchSystemConfig(),
          fetchOllamaStatus(),
          fetchModerationStatus(),
          fetchOllamaModels(),
        ]);
        this.config = config;
        this.ollamaStatus = ollamaStatus;
        this.moderationStatus = moderationStatus;
        this.models = modelInfo.models?.length ? modelInfo.models : [modelInfo.default_model];
        this.defaultModel = modelInfo.default_model || "qwen2.5:3b";
      } finally {
        this.loading = false;
      }
    },
  },
});
