import { Layout as AntLayout, Menu } from "antd";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import {
  MessageOutlined,
  AppstoreOutlined,
  BookOutlined,
  BranchesOutlined,
  SettingOutlined,
} from "@ant-design/icons";

const { Sider, Content } = AntLayout;

const menuItems = [
  { key: "/apps", icon: <AppstoreOutlined />, label: "应用" },
  { key: "/chat", icon: <MessageOutlined />, label: "对话" },
  { key: "/knowledge", icon: <BookOutlined />, label: "知识库" },
  { key: "/workflows", icon: <BranchesOutlined />, label: "工作流" },
  { key: "/settings", icon: <SettingOutlined />, label: "设置" },
];

export default function Layout() {
  const navigate = useNavigate();
  const location = useLocation();

  const selectedKey =
    menuItems.find((item) => location.pathname.startsWith(item.key))?.key ??
    "/apps";

  return (
    <AntLayout style={{ minHeight: "100vh" }}>
      <Sider theme="light" width={200}>
        <div style={{ padding: "16px 24px", fontSize: 18, fontWeight: 600 }}>
          Hify
        </div>
        <Menu
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <AntLayout>
        <Content style={{ padding: 24 }}>
          <Outlet />
        </Content>
      </AntLayout>
    </AntLayout>
  );
}
