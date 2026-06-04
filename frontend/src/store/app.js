import { defineStore } from "pinia";

import {
  fetchConfigBootstrap,
  startOllamaModel,
} from "../api/config";

export const useAppStore = defineStore("app", {
  state: () => ({
    title: import.meta.env.VITE_APP_TITLE || "ChatShield",
    config: null,
    ollamaStatus: null,
    moderationStatus: null,
    models: [],
    runningModels: [],
    activeModel: null,
    defaultModel: "qwen2.5:3b",
    loading: false,
    modelStarting: false,
  }),
  actions: {
    async hydrate(forceRefresh = false) {
      this.loading = true;
      try {
        const bootstrap = await fetchConfigBootstrap(forceRefresh);
        this.config = bootstrap.config;
        this.ollamaStatus = bootstrap.ollama_status;
        this.moderationStatus = bootstrap.moderation_status;
        this.models = bootstrap.models.models || [];
        this.runningModels = bootstrap.models.running_models || [];
        this.activeModel = bootstrap.models.active_model || null;
        this.defaultModel = bootstrap.models.default_model || "qwen2.5:3b";
      } finally {
        this.loading = false;
      }
    },
    async ensureModelStarted(model) {
      this.modelStarting = true;
      try {
        const status = await startOllamaModel(model);
        this.ollamaStatus = status;
        this.runningModels = status.running_models || [];
        this.activeModel = status.active_model || model;
        if (!this.models.includes(model)) {
          this.models = [...this.models, model];
        }
      } finally {
        this.modelStarting = false;
      }
    },
  },
});
