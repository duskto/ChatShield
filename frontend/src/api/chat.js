import http from "./http";

export function sendChatMessage(payload) {
  return http.post("/api/chat", payload);
}

