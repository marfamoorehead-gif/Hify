import { useState } from "react";

interface PaginationState {
  page: number;
  pageSize: number;
}

export function usePagination(defaultPageSize = 20) {
  const [pagination, setPagination] = useState<PaginationState>({
    page: 1,
    pageSize: defaultPageSize,
  });

  const setPage = (page: number) => setPagination((prev) => ({ ...prev, page }));
  const setPageSize = (pageSize: number) =>
    setPagination({ page: 1, pageSize });

  return {
    page: pagination.page,
    pageSize: pagination.pageSize,
    setPage,
    setPageSize,
  };
}
