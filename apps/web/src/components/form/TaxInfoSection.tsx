import { useState } from 'react'
import Field from '@/components/common/Field'
import type { TaxYear, FilingStatus } from '@/types/tax'

interface TaxInfoSectionProps {
  incomeInput: string
  setIncomeInput: (value: string) => void
  combinedIncomeInput: string
  setCombinedIncomeInput: (value: string) => void
  year: TaxYear
  setYear: (value: TaxYear) => void
  hasPHI: boolean
  setHasPHI: (value: boolean) => void
  filingStatus: FilingStatus
  setFilingStatus: (value: FilingStatus) => void
  numChildren: number
  setNumChildren: (value: number) => void
  error: string | null
}

export default function TaxInfoSection({
  incomeInput,
  setIncomeInput,
  combinedIncomeInput,
  setCombinedIncomeInput,
  year,
  setYear,
  hasPHI,
  setHasPHI,
  filingStatus,
  setFilingStatus,
  numChildren,
  setNumChildren,
  error
}: TaxInfoSectionProps) {
  return (
    <>
      <Field label="Your Individual Income" htmlFor="income" hint="Enter your personal annual taxable income. Use shortcuts like 80k." error={error}>
        <input
          id="income"
          value={incomeInput}
          onChange={(e) => setIncomeInput(e.target.value)}
          placeholder="e.g., 85000"
          inputMode="numeric"
          aria-describedby="incomeHint"
          className="w-full px-3.5 py-3 rounded-xl border border-border bg-[#0f1117] text-text outline-none focus:ring-2 focus:ring-accent/40"
        />
      </Field>

      <Field label="Tax Year" htmlFor="year">
        <select
          id="year"
          value={year}
          onChange={(e) => setYear(e.target.value as TaxYear)}
          className="w-full px-3.5 py-3 rounded-xl border border-border bg-[#0f1117] text-text outline-none focus:ring-2 focus:ring-accent/40"
        >
          <option>2024–25</option>
          <option>2023–24</option>
        </select>
      </Field>

      <div className="grid gap-1.5" role="radiogroup" aria-label="Filing status">
        <label className="font-semibold text-sm text-[#cfd3da]">Filing Status</label>
        <div className="flex gap-3.5">
          <label className="inline-flex items-center gap-2">
            <input 
              type="radio" 
              name="filing" 
              checked={filingStatus === 'single'} 
              onChange={() => setFilingStatus('single')} 
            />
            <span>Single</span>
          </label>
          <label className="inline-flex items-center gap-2">
            <input 
              type="radio" 
              name="filing" 
              checked={filingStatus === 'family'} 
              onChange={() => setFilingStatus('family')} 
            />
            <span>Family/Couple</span>
          </label>
        </div>
      </div>

      {filingStatus === 'family' && (
        <>
          <Field label="Combined Family Income" htmlFor="combinedIncome" hint="Total household income for MLS calculation.">
            <input
              id="combinedIncome"
              value={combinedIncomeInput}
              onChange={(e) => setCombinedIncomeInput(e.target.value)}
              placeholder="e.g., 150000"
              inputMode="numeric"
              className="w-full px-3.5 py-3 rounded-xl border border-border bg-[#0f1117] text-text outline-none focus:ring-2 focus:ring-accent/40"
            />
          </Field>

          <Field label="Number of Dependent Children" htmlFor="children">
            <input
              id="children"
              type="number"
              min="0"
              max="10"
              value={numChildren}
              onChange={(e) => setNumChildren(parseInt(e.target.value) || 0)}
              placeholder="0"
              className="w-full px-3.5 py-3 rounded-xl border border-border bg-[#0f1117] text-text outline-none focus:ring-2 focus:ring-accent/40"
            />
          </Field>
        </>
      )}

      <div className="grid gap-1.5" role="radiogroup" aria-label="Private health insurance">
        <label className="font-semibold text-sm text-[#cfd3da]">
          Private Health Insurance {filingStatus === 'family' && '(All Family Members)'}
        </label>
        <div className="flex gap-3.5">
          <label className="inline-flex items-center gap-2">
            <input type="radio" name="phi" checked={hasPHI} onChange={() => setHasPHI(true)} />
            <span>Yes</span>
          </label>
          <label className="inline-flex items-center gap-2">
            <input type="radio" name="phi" checked={!hasPHI} onChange={() => setHasPHI(false)} />
            <span>No</span>
          </label>
        </div>
      </div>
    </>
  )
}