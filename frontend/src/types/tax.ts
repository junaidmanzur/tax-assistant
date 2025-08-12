export type TaxYear = '2024–25' | '2023–24';

export interface TaxRequest {
  income: number; // in AUD
  taxYear: TaxYear;
  hasPrivateHealth: boolean;
}

export interface TaxResponse {
  baseTax: number;
  medicareLevy: number;
  totalTax: number;
}

// Chat-related types
export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  messages: ChatMessage[];
  thread_id?: string;
  config?: Record<string, any>;
}

export interface StreamEvent {
  event: 'step' | 'done' | 'error';
  data: any;
}