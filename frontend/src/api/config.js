import http from "./http";

export function fetchConfigBootstrap(refreshStatus = false) {
  return http.get("/api/config/bootstrap", {
    params: { refresh_status: refreshStatus },
  });
}

export function fetchSystemConfig() {
  return http.get("/api/config");
}

export function fetchOllamaStatus() {
  return http.get("/api/config/ollama/status");
}

export function fetchModerationStatus() {
  return http.get("/api/config/moderation/status");
}

export function fetchOllamaModels() {
  return http.get("/api/config/models");
}
