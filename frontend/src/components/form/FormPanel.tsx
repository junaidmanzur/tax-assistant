import { useMemo, useState } from 'react';
import Field from '@components/common/Field';
import Button from '@components/common/Button';
import { parseIncome } from '@lib/parse';
import { currency } from '@lib/format';
import type { TaxYear, TaxResponse } from '@types/tax';

const API_BASE = import.meta.env.VITE_API_BASE || '';

export default function FormPanel() {
  const [incomeInput, setIncomeInput] = useState('');
  const [year, setYear] = useState<TaxYear>('2024–25');
  const [hasPHI, setHasPHI] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ base: number; levy: number; total: number } | null>(null);

  const parsedIncome = useMemo(() => parseIncome(incomeInput ?? ''), [incomeInput]);

  async function calculate() {
    if (!parsedIncome) {
      setError('Please enter a valid amount (e.g., 85000).');
      setResult(null);
      return;
    }
    setError(null);
    setLoading(true);
    try {
      // Backend API spec: POST { income, hasPrivateHealth, taxYear }
      const res = await fetch(`${API_BASE}/api/calc`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ income: parsedIncome, hasPrivateHealth: hasPHI, taxYear: year }),
      });
      if (!res.ok) throw new Error(`API error: ${res.status}`);
      const data: TaxResponse = await res.json();
      setResult({ base: data.baseTax, levy: data.medicareLevy, total: data.totalTax });
    } catch (e: any) {
      console.error(e);
      setError(e?.message || 'Failed to calculate tax. Please try again.');
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel p-4 grid gap-3.5" aria-label="Form inputs">
      <Field label="Annual Income" htmlFor="income" hint="Enter numbers only. You can use shortcuts like 80k." error={error}>
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

      <div className="grid gap-1.5" role="radiogroup" aria-label="Private health insurance">
        <label className="font-semibold text-sm text-[#cfd3da]">Private Health Insurance</label>
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

      <Button id="calcBtn" type="button" onClick={calculate} loading={loading}>Calculate</Button>

      {result && (
        <div className="grid gap-2 border-t border-dashed border-border pt-3" id="results">
          <div className="kv"><span>Total tax ({year})</span><strong id="r-total">{currency(result.total)}</strong></div>
          <div className="kv"><span>Base tax</span><span id="r-base">{currency(result.base)}</span></div>
          <div className="kv"><span>Medicare Levy</span><span id="r-levy">{currency(result.levy)}</span></div>
        </div>
      )}

      <p className="text-muted text-xs">Data is based on current ATO rules. Estimates are for guidance only. Please consult a professional for complex cases.</p>
    </section>
  );
}