import { Typography, Empty, Button } from "antd";
import { useNavigate } from "react-router-dom";
import { PlusOutlined } from "@ant-design/icons";

const { Title } = Typography;

export default function WorkflowList() {
  const navigate = useNavigate();

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>工作流</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate("/workflows/new")}>
          创建工作流
        </Button>
      </div>
      <Empty description="暂无工作流" />
    </div>
  );
}
