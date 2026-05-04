import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Spin, Result, Typography, Descriptions, Button } from "antd";
import { getApp } from "@/services/app";
import { formatDateTime } from "@/utils/format";
import { APP_TYPE_LABELS } from "@/utils/constants";
import { EditOutlined } from "@ant-design/icons";

const { Title } = Typography;

export default function AppDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: app, isLoading, error } = useQuery({
    queryKey: ["app", id],
    queryFn: () => getApp(id!),
    enabled: !!id,
  });

  if (isLoading) return <Spin />;
  if (error || !app) {
    return <Result status="404" title="应用不存在" />;
  }

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 24 }}>
        <Title level={3} style={{ margin: 0 }}>
          {app.name}
        </Title>
        <Button
          icon={<EditOutlined />}
          onClick={() => navigate(`/apps/${app.id}/edit`)}
        >
          编辑
        </Button>
      </div>

      <Descriptions bordered column={2}>
        <Descriptions.Item label="类型">
          {APP_TYPE_LABELS[app.type] ?? app.type}
        </Descriptions.Item>
        <Descriptions.Item label="模型">{app.model_name}</Descriptions.Item>
        <Descriptions.Item label="描述" span={2}>
          {app.description || "无"}
        </Descriptions.Item>
        <Descriptions.Item label="创建时间">
          {formatDateTime(app.created_at)}
        </Descriptions.Item>
        <Descriptions.Item label="更新时间">
          {formatDateTime(app.updated_at)}
        </Descriptions.Item>
      </Descriptions>
    </div>
  );
}
