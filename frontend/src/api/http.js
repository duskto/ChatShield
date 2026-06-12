import axios from "axios";

const envBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim();

const http = axios.create({
  baseURL: envBaseUrl || "",
  timeout: 120000,
});

http.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error.response?.data?.detail || error.message || "请求失败";
    return Promise.reject(new Error(message));
  },
);

export default http;
