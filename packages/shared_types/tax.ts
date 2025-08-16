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

// Deductions types
export interface CarExpense {
  id: string;
  method: 'cents_per_km' | 'logbook';
  kms?: number;
  work_use_pct?: number;
  // Actual costs for logbook method
  fuel?: number;
  servicing?: number;
  insurance?: number;
  interest_or_lease?: number;
  depreciation?: number;
}

export interface ToolExpense {
  cost: number;
  work_use_pct: number;
}

export interface DeductionsRequest {
  year?: string;
  income: number;
  
  // Working from home
  wfh_hours?: number;
  wfh_use_fixed_rate?: boolean;
  
  // Car expenses
  cars?: CarExpense[];
  
  // Phone & internet
  phone_internet_work_use_pct?: number;
  phone_internet_incidental_claims?: boolean;
  
  // Clothing & laundry
  clothing_work_only_loads?: number;
  clothing_mixed_loads?: number;
  clothing_purchases?: number;
  
  // Tools & equipment
  tools?: ToolExpense[];
  
  // Donations
  donations_dgr_amount?: number;
  donations_bucket_amount?: number;
  donations_is_dgr_confirmed?: boolean;
  
  // Union & professional fees
  union_fees?: number;
  
  // Tax agent fees
  tax_agent_fees?: number;
  
  // Personal super contributions
  personal_super_amount?: number;
}

export interface DeductionLineItem {
  id: string;
  category: string;
  name: string;
  claimed: number;
  allowed: number;
  reason?: string;
  note?: string;
}

export interface DeductionsValidationFlags {
  conflicts: string[];
  warnings: string[];
}

export interface DeductionsPreviewResponse {
  total_allowed: number;
  line_items: DeductionLineItem[];
  engine_flags: DeductionsValidationFlags;
}

export interface TaxCalculationWithDeductionsRequest {
  income: number;
  has_private_health?: boolean;
  filing_status?: 'single' | 'family';
  num_dependent_children?: number;
  combined_family_income_for_mls?: number;
  deductions?: DeductionsRequest;
}

export interface TaxCalculationWithDeductionsResponse {
  // Original tax calculation fields
  base_tax: number;
  medicare_levy: number;
  mls: number;
  lito: number;
  total_tax: number;
  take_home: number;
  
  // Deductions fields (when applicable)
  gross_income: number;
  total_deductions?: number;
  taxable_income: number;
  deductions_breakdown?: DeductionsPreviewResponse;
}