import { useCallback, useEffect, useState } from "react";
import ChatPanel from "./components/ChatPanel";
import CommandBar from "./components/CommandBar";
import DashboardPanel from "./components/DashboardPanel";
import StatusPanel from "./components/StatusPanel";
import type { ChatMessage, MtpData, StatusData } from "./types";
import "./App.css";

export default function App() {
  const [status, setStatus] = useState<StatusData | null>(null);
  const [mtp, setMtp] = useState<MtpData | null>(null);
  const [thinkingMode, setThinkingMode] = useState("think");
  const [systemMessages, setSystemMessages] = useState<ChatMessage[]>([]);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch("/api/status");
      const data: StatusData = await res.json();
      setStatus(data);
      setThinkingMode(data.thinking_mode);
    } catch {
      // backend not ready yet
    }
  }, []);

  const fetchMtp = useCallback(async () => {
    try {
      const res = await fetch("/api/mtp");
      const data: MtpData = await res.json();
      setMtp(data);
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    fetchMtp();
  }, [fetchStatus, fetchMtp]);

  const handleStatusRefresh = useCallback(() => {
    fetchStatus();
    fetchMtp();
  }, [fetchStatus, fetchMtp]);

  const handleBackendChange = useCallback(
    () => {
      handleStatusRefresh();
    },
    [handleStatusRefresh]
  );

  const handleSystemMessage = useCallback((msg: ChatMessage) => {
    setSystemMessages((prev) => [...prev, msg]);
  }, []);

  return (
    <div className="app">
      <CommandBar
        model={status?.model || ""}
        thinkingMode={thinkingMode}
        onThinkingModeChange={setThinkingMode}
        onBackendChange={handleBackendChange}
        onStatusRefresh={handleStatusRefresh}
        onSystemMessage={handleSystemMessage}
      />
      <div className="app-body">
        <ChatPanel
          thinkingMode={thinkingMode}
          onStatusRefresh={handleStatusRefresh}
          systemMessages={systemMessages}
        />
        <div className="right-panels">
          <DashboardPanel status={status} />
          <StatusPanel status={status} mtp={mtp} />
        </div>
      </div>
    </div>
  );
}
