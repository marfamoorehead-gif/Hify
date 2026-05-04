/*
 * @Author: 汪培良 rick_wang@yunquna.com
 * @Date: 2026-05-04 11:56:44
 * @LastEditors: 汪培良 rick_wang@yunquna.com
 * @LastEditTime: 2026-05-04 19:05:35
 * @FilePath: /Hify/frontend/src/pages/apps/AppList.tsx
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
 */
import { useEffect } from "react";
import { Spin, Empty, Card, Button, Typography } from "antd";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { listApps } from "@/services/app";
import { getHealth } from '@/api/health'
import { Pagination } from "@/components/Pagination";
import { usePagination } from "@/hooks/usePagination";
import { APP_TYPE_LABELS } from "@/utils/constants";
import { PlusOutlined } from "@ant-design/icons";
import type { App } from "@/types/app";

const { Title, Text } = Typography;

export default function AppList() {
  const navigate = useNavigate();
  const { page, pageSize, setPage, setPageSize } = usePagination();

  const { data, isLoading, error } = useQuery({
    queryKey: ["apps", page, pageSize],
    queryFn: () => listApps(page, pageSize),
  });
  useEffect(() => {
    const getData = async () => {
      console.log('getData -->')
      const res = await getHealth()
      console.log('res -->' ,res)
    }
    getData()
  }, [])


  if (isLoading) return <Spin />;
  if (error) {
    return (
      <div>
        <Text type="danger">加载失败：{error.message}</Text>
      </div>
    );
  }

  if (!data?.items.length) {
    return (
      <div>
        <div style={{ marginBottom: 16 }}>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => navigate("/apps/new")}
          >
            创建应用
          </Button>
        </div>
        <Empty description="暂无应用" />
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>
          应用列表
        </Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => navigate("/apps/new")}
        >
          创建应用
        </Button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 16 }}>
        {data.items.map((app: App) => (
          <Card
            key={app.id}
            hoverable
            onClick={() => navigate(`/apps/${app.id}`)}
          >
            <Card.Meta
              title={app.name}
              description={
                <>
                  <Text type="secondary">{APP_TYPE_LABELS[app.type] ?? app.type}</Text>
                  {app.description && (
                    <p style={{ marginTop: 8 }}>{app.description}</p>
                  )}
                </>
              }
            />
          </Card>
        ))}
      </div>

      <div style={{ marginTop: 24, textAlign: "right" }}>
        <Pagination
          current={page}
          pageSize={pageSize}
          total={data.total}
          onChange={(newPage, newPageSize) => {
            setPage(newPage);
            setPageSize(newPageSize);
          }}
        />
      </div>
    </div>
  );
}
