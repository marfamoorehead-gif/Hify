import { Typography, Empty, Button } from "antd";
import { useNavigate } from "react-router-dom";
import { PlusOutlined } from "@ant-design/icons";

const { Title } = Typography;

export default function KnowledgeList() {
  const navigate = useNavigate();

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>知识库</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate("/knowledge/new")}>
          创建知识库
        </Button>
      </div>
      <Empty description="暂无知识库" />
    </div>
  );
}
