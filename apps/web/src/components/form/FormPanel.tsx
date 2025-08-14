import { useMemo, useState, useEffect } from 'react';
import Field from '@/components/common/Field';
import Button from '@/components/common/Button';
import { parseIncome } from '@/lib/parse';
import { currency } from '@/lib/format';
import type { TaxYear, FilingStatus } from '@/types/tax';

const API_BASE = import.meta.env.VITE_API_BASE || '';

interface TaxCalculation {
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

interface FormPanelProps {
  syncedCalculation?: TaxCalculation | null;
}

export default function FormPanel({ syncedCalculation }: FormPanelProps) {
  const [incomeInput, setIncomeInput] = useState('');
  const [combinedIncomeInput, setCombinedIncomeInput] = useState('');
  const [year, setYear] = useState<TaxYear>('2024–25');
  const [hasPHI, setHasPHI] = useState(true);
  const [filingStatus, setFilingStatus] = useState<FilingStatus>('single');
  const [numChildren, setNumChildren] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ base: number; levy: number; mls: number; lito: number; total: number; takeHome: number } | null>(null);

  const parsedIncome = useMemo(() => parseIncome(incomeInput ?? ''), [incomeInput]);
  const parsedCombinedIncome = useMemo(() => parseIncome(combinedIncomeInput ?? ''), [combinedIncomeInput]);

  // Sync form fields when new tax calculation comes from ChatPanel
  useEffect(() => {
    if (syncedCalculation) {
      setIncomeInput(syncedCalculation.income.toString());
      setFilingStatus(syncedCalculation.filingStatus);
      setHasPHI(syncedCalculation.hasPrivateHealth);
      setNumChildren(syncedCalculation.numChildren || 0);
      
      // Set combined family income (or clear it if not provided)
      if (syncedCalculation.combinedFamilyIncome) {
        setCombinedIncomeInput(syncedCalculation.combinedFamilyIncome.toString());
      } else {
        setCombinedIncomeInput('');
      }
      
      // Set the result to show the calculation immediately
      setResult({
        base: syncedCalculation.baseTax,
        levy: syncedCalculation.medicareLevy,
        mls: syncedCalculation.mls,
        lito: syncedCalculation.lito,
        total: syncedCalculation.totalTax,
        takeHome: syncedCalculation.takeHome
      });
      
      setError(null);
    }
  }, [syncedCalculation]);

  async function calculate() {
    if (!parsedIncome) {
      setError('Please enter a valid individual income amount (e.g., 85000).');
      setResult(null);
      return;
    }
    
    if (filingStatus === 'family' && !parsedCombinedIncome) {
      setError('Please enter a valid combined family income for MLS calculation.');
      setResult(null);
      return;
    }

    setError(null);
    setLoading(true);
    try {
      // Use the tax calculator tool approach via chat API
      const messages = [
        { 
          role: 'system', 
          content: 'You are an Australian tax assistant. Use the calculate_tax tool directly without asking questions. After using the tool, format the results exactly as: **Base Tax**: $X **Medicare Levy**: $Y **Medicare Levy Surcharge**: $Z **Low Income Tax Offset**: -$W **Total Tax Payable**: $A **Take-Home Income**: $B where the values are from the tool result with proper currency formatting.'
        },
        { 
          role: 'user', 
          content: `Calculate tax for: individual income ${parsedIncome}, filing status ${filingStatus}${
            filingStatus === 'family' ? `, combined family income ${parsedCombinedIncome}, ${numChildren} dependent children` : ''
          }, ${hasPHI ? 'has' : 'no'} private health insurance, tax year ${year}. Please use the calculate_tax tool and provide the exact numerical results.` 
        }
      ];

      const res = await fetch(`${API_BASE}/api/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages, thread_id: `form-${Date.now()}` }),
      });

      if (!res.ok) throw new Error(`API error: ${res.status}`);
      
      // Parse streaming response to extract tax calculation results
      const reader = res.body?.getReader();
      if (!reader) throw new Error('No response body');

      let fullResponse = '';
      const decoder = new TextDecoder();
      let buffer = '';

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const eventData = JSON.parse(line.slice(6));
                if (eventData.ai_content) {
                  fullResponse = eventData.ai_content;
                }
              } catch (e) {
                // Continue processing other lines
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }

      // Look for JSON-like structure or structured data in the response
      let parsedData = null;
      
      // Try to find structured data like "base_tax": 12345.67
      const structuredMatch = fullResponse.match(/\{[^}]*"?base_tax"?\s*:\s*(\d+(?:\.\d{2})?)[^}]*"?medicare_levy"?\s*:\s*(\d+(?:\.\d{2})?)[^}]*"?mls"?\s*:\s*(\d+(?:\.\d{2})?)[^}]*"?total_tax"?\s*:\s*(\d+(?:\.\d{2})?)[^}]*"?take_home"?\s*:\s*(\d+(?:\.\d{2})?)[^}]*\}/i);
      
      if (structuredMatch) {
        parsedData = {
          base: parseFloat(structuredMatch[1]),
          levy: parseFloat(structuredMatch[2]),
          mls: parseFloat(structuredMatch[3]),
          lito: 0, // This format doesn't include LITO separately
          total: parseFloat(structuredMatch[4]),
          takeHome: parseFloat(structuredMatch[5])
        };
      } else {
        // Look for the specific format requested: "base_tax: X, medicare_levy: Y, mls: Z, total_tax: A, take_home: B"
        const formatMatch = fullResponse.match(/base_tax:\s*([0-9,]+(?:\.[0-9]{2})?)[,\s]*medicare_levy:\s*([0-9,]+(?:\.[0-9]{2})?)[,\s]*mls:\s*([0-9,]+(?:\.[0-9]{2})?)[,\s]*total_tax:\s*([0-9,]+(?:\.[0-9]{2})?)[,\s]*take_home:\s*([0-9,]+(?:\.[0-9]{2})?)/i);
        
        if (formatMatch) {
          parsedData = {
            base: parseFloat(formatMatch[1].replace(/,/g, '')),
            levy: parseFloat(formatMatch[2].replace(/,/g, '')),
            mls: parseFloat(formatMatch[3].replace(/,/g, '')),
            lito: 0, // This format doesn't include LITO separately
            total: parseFloat(formatMatch[4].replace(/,/g, '')),
            takeHome: parseFloat(formatMatch[5].replace(/,/g, ''))
          };
        } else {
          // Fallback: look for the exact format our system prompt produces
          const baseMatch = fullResponse.match(/\*\*Base Tax\*\*:\s*\$([0-9,]+(?:\.[0-9]{2})?)/i);
          const medicareMatch = fullResponse.match(/\*\*Medicare Levy\*\*:\s*\$([0-9,]+(?:\.[0-9]{2})?)/i);
          const mlsMatch = fullResponse.match(/\*\*Medicare Levy Surcharge.*?\*\*:\s*\$([0-9,]+(?:\.[0-9]{2})?)/i);
          const litoMatch = fullResponse.match(/\*\*Low Income Tax Offset\*\*:\s*-\$([0-9,]+(?:\.[0-9]{2})?)/i);
          const totalMatch = fullResponse.match(/\*\*Total Tax Payable\*\*:\s*\$([0-9,]+(?:\.[0-9]{2})?)/i);
          const takeHomeMatch = fullResponse.match(/\*\*Take-Home Income\*\*:\s*\$([0-9,]+(?:\.[0-9]{2})?)/i);

          if (baseMatch && medicareMatch && totalMatch) {
            parsedData = {
              base: parseFloat(baseMatch[1].replace(/,/g, '')),
              levy: parseFloat(medicareMatch[1].replace(/,/g, '')),
              mls: mlsMatch ? parseFloat(mlsMatch[1].replace(/,/g, '')) : 0,
              lito: (litoMatch && litoMatch[1]) ? parseFloat(litoMatch[1].replace(/,/g, '')) : 0,
              total: parseFloat(totalMatch[1].replace(/,/g, '')),
              takeHome: takeHomeMatch ? parseFloat(takeHomeMatch[1].replace(/,/g, '')) : parsedIncome - parseFloat(totalMatch[1].replace(/,/g, ''))
            };
          }
        }
      }

      if (parsedData) {
        setResult(parsedData);
      } else {
        throw new Error('Could not parse tax calculation results from response. Please try the chat interface for detailed calculations.');
      }

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

      <Button id="calcBtn" type="button" onClick={calculate} loading={loading}>Calculate</Button>

      {result && (
        <div className="grid gap-2 border-t border-dashed border-border pt-3" id="results">
          <div className="kv"><span>Total tax ({year})</span><strong id="r-total">{currency(result.total)}</strong></div>
          <div className="kv"><span>Take-home pay</span><strong id="r-takehome">{currency(result.takeHome)}</strong></div>
          <div className="kv"><span>Base tax</span><span id="r-base">{currency(result.base)}</span></div>
          <div className="kv"><span>Medicare Levy</span><span id="r-levy">{currency(result.levy)}</span></div>
          <div className="kv"><span>Medicare Levy Surcharge</span><span id="r-mls">{currency(result.mls)}</span></div>
          {result.lito > 0 && (
            <div className="kv"><span>Low Income Tax Offset</span><span id="r-lito" style={{color: '#10b981'}}>-{currency(result.lito)}</span></div>
          )}
        </div>
      )}

      <p className="text-muted text-xs">Data is based on current ATO rules. Estimates are for guidance only. Please consult a professional for complex cases.</p>
    </section>
  );
}