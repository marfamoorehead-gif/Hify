import axios from "axios";
import type { Result } from "@/types/api";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "",
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.response.use(
  (response) => {
    const data = response.data as Result<unknown>;
    if (data.code !== 200) {
      return Promise.reject(new Error(data.message || "请求失败"));
    }
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      window.location.href = "/login";
    }
    if (error.response?.status === 429) {
      return Promise.reject(new Error("请求过于频繁，请稍后再试"));
    }
    if (!error.response) {
      return Promise.reject(new Error("网络异常，请检查网络连接"));
    }
    return Promise.reject(error);
  }
);

export default api;
