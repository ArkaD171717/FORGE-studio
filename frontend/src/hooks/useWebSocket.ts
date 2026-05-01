import { useCallback, useEffect, useRef, useState } from "react";
import type { StreamFrame } from "../types";

type OnFrame = (frame: StreamFrame) => void;

export function useStreamSocket(onFrame: OnFrame) {
  const wsRef = useRef<WebSocket | null>(null);
  const onFrameRef = useRef(onFrame);
  onFrameRef.current = onFrame;
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const url = `${proto}//${window.location.host}/api/chat/stream`;
    const ws = new WebSocket(url);

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (ev) => {
      try {
        const frame: StreamFrame = JSON.parse(ev.data);
        onFrameRef.current(frame);
      } catch {
        // ignore malformed frames
      }
    };

    wsRef.current = ws;
    return () => ws.close();
  }, []);

  const send = useCallback(
    (message: string, mode?: string, maxTokens?: number) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          JSON.stringify({
            message,
            mode: mode || undefined,
            max_tokens: maxTokens || 8192,
          })
        );
      }
    },
    []
  );

  return { send, connected };
}
