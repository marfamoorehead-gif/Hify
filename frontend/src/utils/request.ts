/*
 * @Author: 汪培良 rick_wang@yunquna.com
 * @Date: 2026-05-04 13:04:34
 * @LastEditors: 汪培良 rick_wang@yunquna.com
 * @LastEditTime: 2026-05-04 19:25:57
 * @FilePath: /Hify/frontend/src/utils/request.ts
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
 */
import axios from "axios";
import type { AxiosRequestConfig, AxiosResponse } from "axios";
import { message } from "antd";

interface ApiResponse<T = unknown> {
  code: number;
  message: string;
  data: T;
}

const instance = axios.create({
  baseURL: "/",
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

instance.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    const { code, message: msg, data } = response.data;
    if (code === 200) {
      return data as unknown as AxiosResponse;
    }
    message.error(msg || "请求失败");
    return Promise.reject(new Error(msg || "请求失败"));
  },
  (error) => {
    const msg =
      error.response?.status === 401
        ? "未登录，请重新登录"
        : error.response?.status === 429
          ? "请求过于频繁，请稍后再试"
          : !error.response
            ? "网络异常，请检查网络连接"
            : error.response?.data?.message || "请求失败";

    message.error(msg);

    if (error.response?.status === 401) {
      window.location.href = "/login";
    }

    return Promise.reject(new Error(msg));
  }
);

export function get<T = unknown>(url: string, params?: Record<string, unknown>, config?: AxiosRequestConfig) {
  return instance.get<never, T>(url, { params, ...config });
}

export function post<T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig) {
  return instance.post<never, T>(url, data, config);
}

export function put<T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig) {
  return instance.put<never, T>(url, data, config);
}

export function del<T = unknown>(url: string, config?: AxiosRequestConfig) {
  return instance.delete<never, T>(url, config);
}
