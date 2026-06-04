import http from "./http";

export function fetchConfigBootstrap(refreshStatus = false) {
  return http.get("/api/config/bootstrap", {
    params: { refresh_status: refreshStatus },
  });
}

export function startOllamaModel(model) {
  return http.post("/api/config/models/start", { model });
}
