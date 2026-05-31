import http from "./http";

export function fetchDashboardStats() {
  return http.get("/api/dashboard/stats");
}

