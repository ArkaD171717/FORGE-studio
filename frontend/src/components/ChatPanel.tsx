import { useCallback, useEffect, useRef, useState } from "react";
import type { ChatMessage, StreamFrame } from "../types";
import { useStreamSocket } from "../hooks/useWebSocket";

interface Props {
  thinkingMode: string;
  onStatusRefresh: () => void;
  systemMessages: ChatMessage[];
}

export default function ChatPanel({ thinkingMode, onStatusRefresh, systemMessages }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [thinkingBuf, setThinkingBuf] = useState("");
  const [responseBuf, setResponseBuf] = useState("");
  const [expandedThinking, setExpandedThinking] = useState<Set<number>>(
    new Set()
  );
  const prevSysMsgCount = useRef(0);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (systemMessages.length > prevSysMsgCount.current) {
      const newMsgs = systemMessages.slice(prevSysMsgCount.current);
      setMessages((prev) => [...prev, ...newMsgs]);
      prevSysMsgCount.current = systemMessages.length;
    }
  }, [systemMessages]);

  const onFrame = useCallback(
    (frame: StreamFrame) => {
      if (frame.type === "thinking") {
        setThinkingBuf((prev) => prev + frame.content);
      } else if (frame.type === "response") {
        setResponseBuf((prev) => prev + frame.content);
      } else if (frame.type === "done") {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: frame.full_response || "",
            thinking_content: frame.full_thinking || null,
          },
        ]);
        setThinkingBuf("");
        setResponseBuf("");
        setStreaming(false);
        onStatusRefresh();
      } else if (frame.type === "error") {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: `Error: ${frame.content}` },
        ]);
        setThinkingBuf("");
        setResponseBuf("");
        setStreaming(false);
      }
    },
    [onStatusRefresh]
  );

  const { send, connected } = useStreamSocket(onFrame);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, thinkingBuf, responseBuf]);

  const handleSubmit = () => {
    const trimmed = input.trim();
    if (!trimmed || streaming) return;
    setMessages((prev) => [...prev, { role: "user", content: trimmed }]);
    setStreaming(true);
    setThinkingBuf("");
    setResponseBuf("");
    send(trimmed, thinkingMode);
    setInput("");
  };

  const toggleThinking = (idx: number) => {
    setExpandedThinking((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  };

  const isEmpty = messages.length === 0 && !streaming;

  return (
    <div className="chat-panel">
      <div className="chat-messages">
        {isEmpty && (
          <div className="chat-empty">
            <div className="chat-empty-title">Forge Studio</div>
            <div className="chat-empty-hint">
              Chat with your model, or ingest a repo first using the bar above.
              <br />
              Press <span className="chat-empty-kbd">Enter</span> to send,{" "}
              <span className="chat-empty-kbd">Shift+Enter</span> for newline.
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`chat-msg chat-msg-${msg.role}`}>
            <div className="chat-msg-role">{msg.role}</div>
            {msg.thinking_content && (
              <div className="thinking-block">
                <button
                  className="thinking-toggle"
                  onClick={() => toggleThinking(i)}
                >
                  {expandedThinking.has(i) ? "v" : ">"} thinking
                </button>
                {expandedThinking.has(i) && (
                  <pre className="thinking-content">
                    {msg.thinking_content}
                  </pre>
                )}
              </div>
            )}
            <div className="chat-msg-content">
              <pre>{msg.content}</pre>
            </div>
          </div>
        ))}

        {streaming && (
          <div className="chat-msg chat-msg-assistant">
            <div className="chat-msg-role">assistant</div>
            {thinkingBuf && (
              <div className="thinking-block thinking-streaming">
                <span className="thinking-toggle">... thinking</span>
                <pre className="thinking-content">{thinkingBuf}</pre>
              </div>
            )}
            {responseBuf && (
              <div className="chat-msg-content">
                <pre>{responseBuf}</pre>
              </div>
            )}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <div className="chat-input-area">
        <div className="chat-input-wrapper">
          <textarea
            className="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSubmit();
              }
            }}
            placeholder={
              connected ? "Send a message..." : "Connecting to backend..."
            }
            disabled={!connected || streaming}
            rows={2}
          />
          <button
            className="chat-send"
            onClick={handleSubmit}
            disabled={!connected || streaming || !input.trim()}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
