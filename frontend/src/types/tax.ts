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