import http from "./http";

export function fetchLogs(params) {
  return http.get("/api/logs", { params });
}

export function fetchLogDetail(id) {
  return http.get(`/api/logs/${id}`);
}

