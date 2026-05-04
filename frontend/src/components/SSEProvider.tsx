interface SSEProviderProps {
  children: React.ReactNode;
}

// SSE 连接管理 Provider
// V1 阶段暂不实现，后续在 chat 模块开发时完善
export function SSEProvider({ children }: SSEProviderProps) {
  return <>{children}</>;
}
