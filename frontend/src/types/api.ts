// 后端统一响应格式
export interface Result<T> {
  code: number;
  message: string;
  data: T;
}

// 分页响应
export interface PageResult<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

// 分页请求参数
export interface PageRequest {
  page?: number;
  page_size?: number;
}
