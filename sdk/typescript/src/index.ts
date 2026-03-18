export type Intent =
  | "coding"
  | "reasoning"
  | "classification"
  | "extraction"
  | "summarization"
  | "agent_task"
  | "tool_usage"
  | "conversational"
  | "unknown";

export interface TransformationStep {
  name: string;
  kind: string;
  description: string;
  before?: string | null;
  after?: string | null;
  metadata: Record<string, unknown>;
}

export interface OptimizationScore {
  clarity: number;
  structure: number;
  completeness: number;
  overall: number;
}

export interface OptimizeRequest {
  prompt: string;
  context?: Record<string, unknown>;
}

export interface RunRequest extends OptimizeRequest {
  provider?: string;
  model?: string;
  stream?: boolean;
}

export interface OptimizedPrompt {
  original_prompt: string;
  final_prompt: string;
  intent: Intent;
  skills_applied: string[];
  transformations: TransformationStep[];
  metadata: Record<string, unknown>;
  optimization_score: OptimizationScore;
  prompt_diff: string;
  token_estimate: number;
  latency_ms: number;
}

export interface RunResponse {
  original_prompt: string;
  optimized_prompt: string;
  intent: Intent;
  skills_applied: string[];
  transformations: TransformationStep[];
  provider: string;
  model: string;
  provider_output: string;
  usage: Record<string, unknown>;
  metadata: Record<string, unknown>;
  optimization_score: OptimizationScore;
  prompt_diff: string;
  token_estimate: number;
  latency_ms: number;
  provider_latency_ms: number;
}

export interface PromptEngineClientOptions {
  baseUrl: string;
  apiKey?: string;
  fetchImpl?: typeof fetch;
}

export class PromptEngineClient {
  private readonly baseUrl: string;
  private readonly apiKey?: string;
  private readonly fetchImpl: typeof fetch;

  constructor(options: PromptEngineClientOptions) {
    this.baseUrl = options.baseUrl.replace(/\/$/, "");
    this.apiKey = options.apiKey;
    this.fetchImpl = options.fetchImpl ?? fetch;
  }

  optimize(payload: OptimizeRequest): Promise<OptimizedPrompt> {
    return this.request<OptimizedPrompt>("/optimize", payload);
  }

  optimizeAndRun(payload: RunRequest): Promise<RunResponse> {
    return this.request<RunResponse>("/run", payload);
  }

  async *streamRun(payload: RunRequest): AsyncGenerator<string> {
    const response = await this.fetchImpl(`${this.baseUrl}/run`, {
      method: "POST",
      headers: this.headers(),
      body: JSON.stringify({ ...payload, stream: true }),
    });

    if (!response.ok) {
      throw new Error(`Prompt Engine stream failed: ${response.status} ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error("Readable stream not available.");
    }

    const decoder = new TextDecoder();
    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }
      yield decoder.decode(value, { stream: true });
    }
  }

  private async request<T>(path: string, payload: unknown): Promise<T> {
    const response = await this.fetchImpl(`${this.baseUrl}${path}`, {
      method: "POST",
      headers: this.headers(),
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`Prompt Engine request failed: ${response.status} ${response.statusText}`);
    }

    return (await response.json()) as T;
  }

  private headers(): HeadersInit {
    const headers: HeadersInit = {
      "Content-Type": "application/json",
    };
    if (this.apiKey) {
      headers["Authorization"] = `Bearer ${this.apiKey}`;
    }
    return headers;
  }
}

