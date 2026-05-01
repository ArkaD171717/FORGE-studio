import { useState } from "react";
import type { ChatMessage } from "../types";

interface Props {
  model: string;
  thinkingMode: string;
  onThinkingModeChange: (mode: string) => void;
  onBackendChange: () => void;
  onStatusRefresh: () => void;
  onSystemMessage: (msg: ChatMessage) => void;
}

export default function CommandBar({
  model,
  thinkingMode,
  onThinkingModeChange,
  onBackendChange,
  onStatusRefresh,
  onSystemMessage,
}: Props) {
  const [ingestInput, setIngestInput] = useState("");
  const [ingesting, setIngesting] = useState(false);

  const handleIngest = async () => {
    const val = ingestInput.trim();
    if (!val || ingesting) return;
    setIngesting(true);

    const isUrl = val.startsWith("http://") || val.startsWith("https://") || val.startsWith("git@");
    const endpoint = isUrl ? "/api/ingest" : "/api/ingest-local";
    const body = isUrl ? { repo_url: val } : { path: val };

    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (data.ok) {
        onSystemMessage({
          role: "system",
          content: `Ingested ${val} -- ${data.tokens.toLocaleString()} tokens added to context.`,
        });
        setIngestInput("");
        onStatusRefresh();
      } else {
        onSystemMessage({
          role: "system",
          content: `Ingest failed: ${data.error}`,
        });
      }
    } catch (e) {
      onSystemMessage({
        role: "system",
        content: `Ingest failed: ${e}`,
      });
    } finally {
      setIngesting(false);
    }
  };

  const handleThinkingToggle = async () => {
    const next = thinkingMode === "think" ? "no_think" : "think";
    try {
      const res = await fetch("/api/thinking-mode", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode: next }),
      });
      const data = await res.json();
      if (data.ok) {
        onThinkingModeChange(next);
      }
    } catch {
      // ignore
    }
  };

  const handleBackendChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    try {
      const res = await fetch("/api/backend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ backend: val }),
      });
      const data = await res.json();
      if (data.ok) {
        onBackendChange();
        onStatusRefresh();
      }
    } catch {
      // ignore
    }
  };

  const isThinking = thinkingMode === "think";

  return (
    <div className="command-bar">
      <div className="cmd-group">
        <input
          className="cmd-input"
          value={ingestInput}
          onChange={(e) => setIngestInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleIngest();
          }}
          placeholder="Repo URL or local path..."
          disabled={ingesting}
        />
        <button className="cmd-btn" onClick={handleIngest} disabled={ingesting}>
          {ingesting ? "Ingesting..." : "Ingest"}
        </button>
      </div>

      <div className="cmd-group">
        <div className="toggle-switch" onClick={handleThinkingToggle}>
          <span className="toggle-switch-label">Thinking</span>
          <div className={`toggle-track ${isThinking ? "on" : ""}`}>
            <div className="toggle-knob" />
          </div>
        </div>
      </div>

      <div className="cmd-group">
        <select className="cmd-select" onChange={handleBackendChange} defaultValue="">
          <option value="" disabled>Backend</option>
          <option value="vllm">vLLM</option>
          <option value="sglang">SGLang</option>
          <option value="dashscope">DashScope</option>
        </select>
      </div>

      <div className="cmd-group cmd-model">
        <span className="cmd-label">{model || "No model"}</span>
      </div>
    </div>
  );
}
