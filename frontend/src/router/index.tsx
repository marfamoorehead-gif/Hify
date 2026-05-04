import { createBrowserRouter } from "react-router-dom";
import Layout from "@/components/Layout";
import AppList from "@/pages/apps/AppList";
import AppCreate from "@/pages/apps/AppCreate";
import AppDetail from "@/pages/apps/AppDetail";
import ChatPage from "@/pages/chat/ChatPage";
import KnowledgeList from "@/pages/knowledge/KnowledgeList";
import KnowledgeDetail from "@/pages/knowledge/KnowledgeDetail";
import WorkflowList from "@/pages/workflow/WorkflowList";
import WorkflowEditor from "@/pages/workflow/WorkflowEditor";
import Settings from "@/pages/settings/Settings";
import NotFound from "@/pages/NotFound";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout />,
    children: [
      { index: true, element: <AppList /> },
      { path: "apps", element: <AppList /> },
      { path: "apps/new", element: <AppCreate /> },
      { path: "apps/:id", element: <AppDetail /> },
      { path: "apps/:id/edit", element: <AppCreate /> },
      { path: "chat", element: <ChatPage /> },
      { path: "chat/:appId", element: <ChatPage /> },
      { path: "chat/:appId/:conversationId", element: <ChatPage /> },
      { path: "knowledge", element: <KnowledgeList /> },
      { path: "knowledge/new", element: <KnowledgeDetail /> },
      { path: "knowledge/:id", element: <KnowledgeDetail /> },
      { path: "workflows", element: <WorkflowList /> },
      { path: "workflows/new", element: <WorkflowEditor /> },
      { path: "workflows/:id", element: <WorkflowEditor /> },
      { path: "settings", element: <Settings /> },
      { path: "*", element: <NotFound /> },
    ],
  },
]);
