export type TaxYear = '2024–25' | '2023–24';
export type FilingStatus = 'single' | 'family';

export interface TaxRequest {
  income: number; // in AUD
  taxYear: TaxYear;
  hasPrivateHealth: boolean;
  filingStatus?: FilingStatus;
  numDependentChildren?: number;
  combinedFamilyIncomeForMLS?: number;
}

export interface TaxResponse {
  baseTax: number;
  medicareLevy: number;
  mls: number;
  totalTax: number;
  takeHome: number;
}

export interface TaxCalculation {
  income: number;
  baseTax: number;
  medicareLevy: number;
  mls: number;
  lito: number;
  totalTax: number;
  takeHome: number;
  filingStatus: 'single' | 'family';
  combinedFamilyIncome?: number;
  numChildren?: number;
  hasPrivateHealth: boolean;
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