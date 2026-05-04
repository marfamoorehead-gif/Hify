import { useParams } from "react-router-dom";
import { Typography } from "antd";

const { Title } = Typography;

export default function KnowledgeDetail() {
  const { id } = useParams<{ id: string }>();

  return (
    <div>
      <Title level={3}>{id ? "知识库详情" : "创建知识库"}</Title>
      <p>知识库管理功能开发中...</p>
    </div>
  );
}
