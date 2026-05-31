import http from "./http";

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
