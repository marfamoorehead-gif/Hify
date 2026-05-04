import { Pagination as AntPagination } from "antd";

interface PaginationProps {
  current: number;
  pageSize: number;
  total: number;
  onChange: (page: number, pageSize: number) => void;
}

export function Pagination({ current, pageSize, total, onChange }: PaginationProps) {
  return (
    <AntPagination
      current={current}
      pageSize={pageSize}
      total={total}
      onChange={onChange}
      showSizeChanger
      showTotal={(total) => `共 ${total} 条`}
    />
  );
}
