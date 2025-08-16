import { currency } from '@/lib/format'
import type { TaxYear } from '@/types/tax'

interface TaxResult {
  base: number
  levy: number
  mls: number
  lito: number
  total: number
  takeHome: number
  grossIncome?: number
  totalDeductions?: number
  taxableIncome?: number
}

interface TaxResultsProps {
  result: TaxResult
  year: TaxYear
}

export default function TaxResults({ result, year }: TaxResultsProps) {
  const hasDeductions = result.totalDeductions && result.totalDeductions > 0;
  
  return (
    <div className="grid gap-2 border-t border-dashed border-border pt-3" id="results">
      {/* Show deductions breakdown if available */}
      {hasDeductions && (
        <>
          <div className="kv">
            <span>Gross income</span>
            <span id="r-gross">{currency(result.grossIncome || 0)}</span>
          </div>
          <div className="kv">
            <span>Total deductions</span>
            <span id="r-deductions" style={{color: '#10b981'}}>-{currency(result.totalDeductions)}</span>
          </div>
          <div className="kv">
            <span>Taxable income</span>
            <strong id="r-taxable">{currency(result.taxableIncome || 0)}</strong>
          </div>
          <div className="border-t border-dashed border-border pt-2 mt-2"></div>
        </>
      )}
      
      <div className="kv">
        <span>Total tax ({year})</span>
        <strong id="r-total">{currency(result.total)}</strong>
      </div>
      <div className="kv">
        <span>Take-home pay</span>
        <strong id="r-takehome">{currency(result.takeHome)}</strong>
      </div>
      <div className="kv">
        <span>Base tax</span>
        <span id="r-base">{currency(result.base)}</span>
      </div>
      <div className="kv">
        <span>Medicare Levy</span>
        <span id="r-levy">{currency(result.levy)}</span>
      </div>
      <div className="kv">
        <span>Medicare Levy Surcharge</span>
        <span id="r-mls">{currency(result.mls)}</span>
      </div>
      {result.lito > 0 && (
        <div className="kv">
          <span>Low Income Tax Offset</span>
          <span id="r-lito" style={{color: '#10b981'}}>-{currency(result.lito)}</span>
        </div>
      )}
    </div>
  )
}