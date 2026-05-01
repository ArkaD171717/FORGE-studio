import { useState } from "react";
import type { StatusData, MtpData } from "../types";

interface Props {
  status: StatusData | null;
  mtp: MtpData | null;
}

export default function StatusPanel({ status, mtp }: Props) {
  const [copiedField, setCopiedField] = useState<string | null>(null);

  const copy = (text: string, field: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 1500);
  };

  if (!status) {
    return (
      <div className="status-panel">
        <h3>Status</h3>
        <p className="muted">Connecting...</p>
      </div>
    );
  }

  return (
    <div className="status-panel">
      <h3>Status</h3>

      <div className="status-row">
        <span className="status-key">Model</span>
        <span className="status-val">{status.model}</span>
      </div>
      <div className="status-row">
        <span className="status-key">Backend</span>
        <span className="status-val">{status.backend}</span>
      </div>
      <div className="status-row">
        <span className="status-key">Base URL</span>
        <span className="status-val mono">{status.base_url}</span>
      </div>
      <div className="status-row">
        <span className="status-key">Messages</span>
        <span className="status-val">{status.messages}</span>
      </div>

      {status.context && (
        <>
          <div className="status-divider" />
          <div className="status-row">
            <span className="status-key">Context tokens</span>
            <span className="status-val">
              {status.context.tokens.toLocaleString()}
            </span>
          </div>
          <div className="status-row">
            <span className="status-key">Files ingested</span>
            <span className="status-val">{status.context.files}</span>
          </div>
        </>
      )}

      {mtp && mtp.available && (
        <>
          <div className="status-divider" />
          <div className="status-subtitle">MTP Recommendation</div>
          <div className="status-row">
            <span className="status-key">Enable</span>
            <span className={`status-val ${mtp.enable ? "text-green" : "text-amber"}`}>
              {mtp.enable ? "Yes" : "No"}
            </span>
          </div>
          {mtp.expected_gain && (
            <div className="status-row">
              <span className="status-key">Expected gain</span>
              <span className="status-val">{mtp.expected_gain}</span>
            </div>
          )}
          {mtp.num_speculative_tokens !== undefined && (
            <div className="status-row">
              <span className="status-key">Spec tokens</span>
              <span className="status-val">{mtp.num_speculative_tokens}</span>
            </div>
          )}
          {mtp.warnings && mtp.warnings.length > 0 && (
            <div className="status-warnings">
              {mtp.warnings.map((w, i) => (
                <div key={i} className="status-warning">{w}</div>
              ))}
            </div>
          )}
          {mtp.vllm_command && (
            <div className="status-cmd">
              <code>{mtp.vllm_command}</code>
              <button
                className="copy-btn"
                onClick={() => copy(mtp.vllm_command!, "vllm")}
              >
                {copiedField === "vllm" ? "Copied" : "Copy"}
              </button>
            </div>
          )}
          {mtp.sglang_command && (
            <div className="status-cmd">
              <code>{mtp.sglang_command}</code>
              <button
                className="copy-btn"
                onClick={() => copy(mtp.sglang_command!, "sglang")}
              >
                {copiedField === "sglang" ? "Copied" : "Copy"}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
