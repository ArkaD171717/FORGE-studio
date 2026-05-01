export interface StatusData {
  model: string;
  model_hf: string;
  backend: string;
  base_url: string;
  thinking_mode: string;
  budget: {
    total: number;
    used: number;
    available: number;
    action: string;
  };
  messages: number;
  mtp?: {
    enable: boolean;
    num_speculative_tokens: number;
    expected_gain: string;
    warnings: string[];
    vllm_command?: string;
    sglang_command?: string;
  };
  context?: {
    tokens: number;
    files: number;
  };
}

export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
  thinking_content?: string | null;
  token_count?: number;
}

export interface StreamFrame {
  type: "thinking" | "response" | "done" | "error";
  content: string;
  full_thinking?: string;
  full_response?: string;
}

export interface MtpData {
  available: boolean;
  enable?: boolean;
  reason?: string;
  num_speculative_tokens?: number;
  expected_gain?: string;
  warnings?: string[];
  vllm_command?: string;
  sglang_command?: string;
}
