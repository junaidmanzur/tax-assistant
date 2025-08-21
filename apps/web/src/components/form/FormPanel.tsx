import { useMemo, useState, useEffect } from 'react';
import Button from '@/components/common/Button';
import { parseIncome } from '@/lib/parse';
import type { TaxYear, FilingStatus, TaxCalculation } from '@/types/tax';
import TaxInfoSection from './TaxInfoSection';
import DeductionsSection from './DeductionsSection';
import TaxResults from './TaxResults';
import { useDeductionsStore } from '../../store/deductionsStore';

const API_BASE = import.meta.env.VITE_API_BASE || '';

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
  const [result, setResult] = useState<{ 
    base: number; 
    levy: number; 
    mls: number; 
    lito: number; 
    total: number; 
    takeHome: number;
    grossIncome?: number;
    totalDeductions?: number;
    taxableIncome?: number;
  } | null>(null);
  
  // Deductions store hooks
  const setWFHHours = useDeductionsStore(state => state.setWFHHours);
  const setWFHFixedRate = useDeductionsStore(state => state.setWFHFixedRate);
  const addCar = useDeductionsStore(state => state.addCar);
  const updateCar = useDeductionsStore(state => state.updateCar);
  const setPhoneInternetWorkPct = useDeductionsStore(state => state.setPhoneInternetWorkPct);
  const setPhoneInternetIncidental = useDeductionsStore(state => state.setPhoneInternetIncidental);
  const setClothingWorkOnlyLoads = useDeductionsStore(state => state.setClothingWorkOnlyLoads);
  const setClothingMixedLoads = useDeductionsStore(state => state.setClothingMixedLoads);
  const setClothingPurchases = useDeductionsStore(state => state.setClothingPurchases);
  const addTool = useDeductionsStore(state => state.addTool);
  const updateTool = useDeductionsStore(state => state.updateTool);
  const setDonationsDGRAmount = useDeductionsStore(state => state.setDonationsDGRAmount);
  const setDonationsBucketAmount = useDeductionsStore(state => state.setDonationsBucketAmount);
  const setDonationsDGRConfirmed = useDeductionsStore(state => state.setDonationsDGRConfirmed);
  const setUnionFees = useDeductionsStore(state => state.setUnionFees);
  const setTaxAgentFees = useDeductionsStore(state => state.setTaxAgentFees);
  const setPersonalSuperAmount = useDeductionsStore(state => state.setPersonalSuperAmount);
  
  // Get current deductions state for calculation
  const deductionsState = useDeductionsStore();
  

  const parsedIncome = useMemo(() => parseIncome(incomeInput ?? ''), [incomeInput]);
  const parsedCombinedIncome = useMemo(() => parseIncome(combinedIncomeInput ?? ''), [combinedIncomeInput]);

  // Sync form fields when new tax calculation comes from ChatPanel
  useEffect(() => {
    if (syncedCalculation) {
      // Sync basic tax info
      setIncomeInput((syncedCalculation.grossIncome || syncedCalculation.income).toString());
      setFilingStatus(syncedCalculation.filingStatus);
      setHasPHI(syncedCalculation.hasPrivateHealth);
      setNumChildren(syncedCalculation.numChildren || 0);
      
      // Set combined family income (or clear it if not provided)
      if (syncedCalculation.combinedFamilyIncome) {
        setCombinedIncomeInput(syncedCalculation.combinedFamilyIncome.toString());
      } else {
        setCombinedIncomeInput('');
      }
      
      // Sync deductions data if available
      if (syncedCalculation.deductionsBreakdown) {
        const deductions = syncedCalculation.deductionsBreakdown;
        
        // Working from home
        if (deductions.wfh_hours !== undefined) {
          setWFHHours(deductions.wfh_hours);
        }
        if (deductions.wfh_use_fixed_rate !== undefined) {
          setWFHFixedRate(deductions.wfh_use_fixed_rate);
        }
        
        // Phone & internet
        if (deductions.phone_internet_work_use_pct !== undefined) {
          setPhoneInternetWorkPct(deductions.phone_internet_work_use_pct);
        }
        if (deductions.phone_internet_incidental_claims !== undefined) {
          setPhoneInternetIncidental(deductions.phone_internet_incidental_claims);
        }
        
        // Clothing & laundry
        if (deductions.clothing_work_only_loads !== undefined) {
          setClothingWorkOnlyLoads(deductions.clothing_work_only_loads);
        }
        if (deductions.clothing_mixed_loads !== undefined) {
          setClothingMixedLoads(deductions.clothing_mixed_loads);
        }
        if (deductions.clothing_purchases !== undefined) {
          setClothingPurchases(deductions.clothing_purchases);
        }
        
        // Donations
        if (deductions.donations_dgr_amount !== undefined) {
          setDonationsDGRAmount(deductions.donations_dgr_amount);
        }
        if (deductions.donations_bucket_amount !== undefined) {
          setDonationsBucketAmount(deductions.donations_bucket_amount);
        }
        if (deductions.donations_is_dgr_confirmed !== undefined) {
          setDonationsDGRConfirmed(deductions.donations_is_dgr_confirmed);
        }
        
        // Other deductions
        if (deductions.union_fees !== undefined) {
          setUnionFees(deductions.union_fees);
        }
        if (deductions.tax_agent_fees !== undefined) {
          setTaxAgentFees(deductions.tax_agent_fees);
        }
        if (deductions.personal_super_amount !== undefined) {
          setPersonalSuperAmount(deductions.personal_super_amount);
        }
        
        // TODO: Handle cars and tools arrays
        // These would need more complex logic to sync properly
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
  }, [syncedCalculation, setWFHHours, setWFHFixedRate, setPhoneInternetWorkPct, setPhoneInternetIncidental, setClothingWorkOnlyLoads, setClothingMixedLoads, setClothingPurchases, setDonationsDGRAmount, setDonationsBucketAmount, setDonationsDGRConfirmed, setUnionFees, setTaxAgentFees, setPersonalSuperAmount]);

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
      // Check if there are any deductions to include
      const hasDeductions = deductionsState.wfh_hours || 
                           deductionsState.cars.length > 0 ||
                           deductionsState.phone_internet_work_use_pct ||
                           deductionsState.phone_internet_incidental_claims ||
                           deductionsState.clothing_work_only_loads ||
                           deductionsState.clothing_mixed_loads ||
                           deductionsState.clothing_purchases ||
                           deductionsState.tools.length > 0 ||
                           deductionsState.donations_dgr_amount ||
                           deductionsState.donations_bucket_amount ||
                           deductionsState.union_fees ||
                           deductionsState.tax_agent_fees ||
                           deductionsState.personal_super_amount;

      // Use the tax calculator tool approach via chat API
      const messages = [
        { 
          role: 'system', 
          content: hasDeductions 
            ? 'You are an Australian tax assistant. First use the calculate_deductions tool with the provided deduction details, then use the calculate_tax tool with the deductions data. Format the results exactly as: **Gross Income**: $X **Total Deductions**: $Y **Taxable Income**: $Z **Base Tax**: $A **Medicare Levy**: $B **Medicare Levy Surcharge**: $C **Low Income Tax Offset**: -$D **Total Tax Payable**: $E **Take-Home Income**: $F where the values are from the tool results with proper currency formatting.'
            : 'You are an Australian tax assistant. Use the calculate_tax tool directly without asking questions. After using the tool, format the results exactly as: **Base Tax**: $X **Medicare Levy**: $Y **Medicare Levy Surcharge**: $Z **Low Income Tax Offset**: -$W **Total Tax Payable**: $A **Take-Home Income**: $B where the values are from the tool result with proper currency formatting.'
        },
        { 
          role: 'user', 
          content: hasDeductions
            ? `Calculate tax with deductions for: individual income ${parsedIncome}, filing status ${filingStatus}${
                filingStatus === 'family' ? `, combined family income ${parsedCombinedIncome}, ${numChildren} dependent children` : ''
              }, ${hasPHI ? 'has' : 'no'} private health insurance, tax year ${year}. 
              
              Deductions:
              ${deductionsState.wfh_hours ? `- Working from home: ${deductionsState.wfh_hours} hours, fixed rate method: ${deductionsState.wfh_use_fixed_rate}` : ''}
              ${deductionsState.cars.map((car, i) => `- Car ${i+1}: ${car.method}, ${car.kms ? car.kms + ' km' : ''} ${car.work_use_pct ? car.work_use_pct + '% work use' : ''}`).join('\n')}
              ${deductionsState.phone_internet_work_use_pct ? `- Phone/Internet: ${deductionsState.phone_internet_work_use_pct}% work use` : ''}
              ${deductionsState.phone_internet_incidental_claims ? '- Phone/Internet: incidental claims ($50)' : ''}
              ${deductionsState.clothing_work_only_loads ? `- Clothing: ${deductionsState.clothing_work_only_loads} work-only loads` : ''}
              ${deductionsState.clothing_mixed_loads ? `- Clothing: ${deductionsState.clothing_mixed_loads} mixed loads` : ''}
              ${deductionsState.clothing_purchases ? `- Clothing purchases: $${deductionsState.clothing_purchases}` : ''}
              ${deductionsState.tools.map((tool, i) => `- Tool ${i+1}: $${tool.cost}, ${tool.work_use_pct}% work use`).join('\n')}
              ${deductionsState.donations_dgr_amount ? `- DGR donations: $${deductionsState.donations_dgr_amount}` : ''}
              ${deductionsState.donations_bucket_amount ? `- Bucket donations: $${deductionsState.donations_bucket_amount}` : ''}
              ${deductionsState.union_fees ? `- Union fees: $${deductionsState.union_fees}` : ''}
              ${deductionsState.tax_agent_fees ? `- Tax agent fees: $${deductionsState.tax_agent_fees}` : ''}
              ${deductionsState.personal_super_amount ? `- Personal super: $${deductionsState.personal_super_amount}` : ''}
              
              Please first calculate the deductions, then calculate the tax with those deductions applied.`
            : `Calculate tax for: individual income ${parsedIncome}, filing status ${filingStatus}${
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
          // Fallback: look for the exact format our system prompt produces (with or without deductions)
          const grossMatch = fullResponse.match(/\*\*Gross Income\*\*:\s*\$([0-9,]+(?:\.[0-9]{2})?)/i);
          const deductionsMatch = fullResponse.match(/\*\*Total Deductions\*\*:\s*\$([0-9,]+(?:\.[0-9]{2})?)/i);
          const taxableMatch = fullResponse.match(/\*\*Taxable Income\*\*:\s*\$([0-9,]+(?:\.[0-9]{2})?)/i);
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
            
            // Add deductions information if available
            if (grossMatch && deductionsMatch && taxableMatch) {
              parsedData.grossIncome = parseFloat(grossMatch[1].replace(/,/g, ''));
              parsedData.totalDeductions = parseFloat(deductionsMatch[1].replace(/,/g, ''));
              parsedData.taxableIncome = parseFloat(taxableMatch[1].replace(/,/g, ''));
            }
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
    <>
      <section className="panel p-4 grid gap-3.5" aria-label="Form inputs">
        <TaxInfoSection
          incomeInput={incomeInput}
          setIncomeInput={setIncomeInput}
          combinedIncomeInput={combinedIncomeInput}
          setCombinedIncomeInput={setCombinedIncomeInput}
          year={year}
          setYear={setYear}
          hasPHI={hasPHI}
          setHasPHI={setHasPHI}
          filingStatus={filingStatus}
          setFilingStatus={setFilingStatus}
          numChildren={numChildren}
          setNumChildren={setNumChildren}
          error={error}
        />

        <DeductionsSection />

        <Button id="calcBtn" type="button" onClick={calculate} loading={loading}>Calculate</Button>

        {result && <TaxResults result={result} year={year} />}

      <p className="text-muted text-xs">Data is based on current ATO rules. Estimates are for guidance only. Please consult a professional for complex cases.</p>
      </section>
      
    </>
  );
}