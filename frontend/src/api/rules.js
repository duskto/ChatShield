import http from "./http";

export function fetchRules() {
  return http.get("/api/rules");
}

export function createRule(payload) {
  return http.post("/api/rules", payload);
}

export function updateRule(id, payload) {
  return http.put(`/api/rules/${id}`, payload);
}

export function deleteRule(id) {
  return http.delete(`/api/rules/${id}`);
}

