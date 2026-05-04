import { useState, useCallback, useRef, useEffect } from "react";

interface SSEResult {
  data: string;
  isStreaming: boolean;
  error: Error | null;
  abort: () => void;
}

export function useSSE(_url: string, _body: Record<string, unknown>): SSEResult {
  const [data] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [error] = useState<Error | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const abort = useCallback(() => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    setIsStreaming(false);
  }, []);

  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  // TODO: 实现 SSE 连接逻辑（fetchEventSource）
  // 连接后端 SSE 端点，逐 token 累加 data，通过 chatStore.updateMessage 更新消息

  return { data, isStreaming, error, abort };
}
