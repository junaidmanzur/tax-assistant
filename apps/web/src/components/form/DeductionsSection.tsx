import { useState, useEffect } from 'react'
import Button from '@/components/common/Button'
import Field from '@/components/common/Field'
import { useDeductionsStore, useFeatureFlag } from '../../store/deductionsStore'

interface DeductionsSectionProps {
  // Props can be added as needed
}

export default function DeductionsSection({}: DeductionsSectionProps) {
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({})
  
  // Feature flag management - simplified for development
  const { enabled: featureEnabled } = useFeatureFlag()
  
  // Don't render if feature is disabled
  if (!featureEnabled) {
    return null
  }
  
  // Get deductions data from store
  const wfh_hours = useDeductionsStore(state => state.wfh_hours)
  const wfh_use_fixed_rate = useDeductionsStore(state => state.wfh_use_fixed_rate)
  const setWFHHours = useDeductionsStore(state => state.setWFHHours)
  const setWFHFixedRate = useDeductionsStore(state => state.setWFHFixedRate)
  
  const cars = useDeductionsStore(state => state.cars)
  const addCar = useDeductionsStore(state => state.addCar)
  const updateCar = useDeductionsStore(state => state.updateCar)
  const removeCar = useDeductionsStore(state => state.removeCar)
  
  const phone_internet_work_use_pct = useDeductionsStore(state => state.phone_internet_work_use_pct)
  const phone_internet_incidental_claims = useDeductionsStore(state => state.phone_internet_incidental_claims)
  const setPhoneInternetWorkPct = useDeductionsStore(state => state.setPhoneInternetWorkPct)
  const setPhoneInternetIncidental = useDeductionsStore(state => state.setPhoneInternetIncidental)
  
  const clothing_work_only_loads = useDeductionsStore(state => state.clothing_work_only_loads)
  const clothing_mixed_loads = useDeductionsStore(state => state.clothing_mixed_loads)
  const clothing_purchases = useDeductionsStore(state => state.clothing_purchases)
  const setClothingWorkOnlyLoads = useDeductionsStore(state => state.setClothingWorkOnlyLoads)
  const setClothingMixedLoads = useDeductionsStore(state => state.setClothingMixedLoads)
  const setClothingPurchases = useDeductionsStore(state => state.setClothingPurchases)
  
  const tools = useDeductionsStore(state => state.tools)
  const addTool = useDeductionsStore(state => state.addTool)
  const updateTool = useDeductionsStore(state => state.updateTool)
  const removeTool = useDeductionsStore(state => state.removeTool)
  
  const donations_dgr_amount = useDeductionsStore(state => state.donations_dgr_amount)
  const donations_bucket_amount = useDeductionsStore(state => state.donations_bucket_amount)
  const donations_is_dgr_confirmed = useDeductionsStore(state => state.donations_is_dgr_confirmed)
  const setDonationsDGRAmount = useDeductionsStore(state => state.setDonationsDGRAmount)
  const setDonationsBucketAmount = useDeductionsStore(state => state.setDonationsBucketAmount)
  const setDonationsDGRConfirmed = useDeductionsStore(state => state.setDonationsDGRConfirmed)
  
  const union_fees = useDeductionsStore(state => state.union_fees)
  const setUnionFees = useDeductionsStore(state => state.setUnionFees)
  
  const tax_agent_fees = useDeductionsStore(state => state.tax_agent_fees)
  const setTaxAgentFees = useDeductionsStore(state => state.setTaxAgentFees)
  
  const personal_super_amount = useDeductionsStore(state => state.personal_super_amount)
  const setPersonalSuperAmount = useDeductionsStore(state => state.setPersonalSuperAmount)
  
  // Calculate total deductions for summary
  const wfhDeductions = (wfh_hours || 0) * 0.7
  const carDeductions = cars.reduce((total, car) => {
    if (car.method === 'cents_per_km' && car.kms) {
      return total + (car.kms * 0.88) // 2024-25 rate: 88 cents per km
    }
    return total
  }, 0)
  const phoneDeductions = phone_internet_incidental_claims ? 50 : (phone_internet_work_use_pct ? 0 : 0) // Simplified estimate
  const clothingDeductions = ((clothing_work_only_loads || 0) * 1.0) + ((clothing_mixed_loads || 0) * 0.5) + (clothing_purchases || 0)
  const toolsDeductions = tools.reduce((total, tool) => {
    if (tool.cost && tool.work_use_pct) {
      return total + (tool.cost * (tool.work_use_pct / 100))
    }
    return total
  }, 0)
  const donationsDeductions = (donations_dgr_amount || 0) + (donations_bucket_amount || 0)
  const unionDeductions = union_fees || 0
  const taxAgentDeductions = tax_agent_fees || 0
  const superDeductions = personal_super_amount || 0
  
  const totalDeductions = wfhDeductions + carDeductions + phoneDeductions + clothingDeductions + toolsDeductions + donationsDeductions + unionDeductions + taxAgentDeductions + superDeductions
  const hasAnyDeductions = totalDeductions > 0

  const toggleSection = (sectionId: string) => {
    setExpandedSections(prev => ({ ...prev, [sectionId]: !prev[sectionId] }))
  }

  const quickAddCommon = () => {
    // Quick add common deductions - can be expanded later
    setExpandedSections({ wfh: true, car: true })
  }

  return (
    <div className="border-t border-dashed border-border pt-6 mt-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-text">Deductions (Optional)</h3>
        <Button
          type="button"
          onClick={quickAddCommon}
          className="text-sm bg-accent/10 border border-accent/30 text-accent hover:bg-accent/20"
        >
          Quick Add
        </Button>
      </div>
      
      <div className="space-y-3">
        {/* Working from Home Section */}
        <InlineDeductionSection
          id="wfh"
          title="Working from Home"
          expanded={expandedSections.wfh}
          onToggle={() => toggleSection('wfh')}
          hasValue={!!wfh_hours}
          estimatedValue={wfh_hours ? (wfh_hours * 0.7).toFixed(2) : '0'}
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Hours per year" htmlFor="wfh-hours" className="mb-0">
              <input
                id="wfh-hours"
                type="number"
                min="0"
                max="2000"
                value={wfh_hours || ''}
                onChange={(e) => setWFHHours(parseInt(e.target.value) || undefined)}
                placeholder="e.g., 365"
                className="w-full px-3 py-2 bg-[#0a0b0e] border border-border rounded-lg text-text focus:ring-2 focus:ring-accent/40"
              />
            </Field>
            <div className="flex items-end">
              <label className="flex items-center gap-2 text-sm text-text">
                <input
                  type="checkbox"
                  checked={wfh_use_fixed_rate}
                  onChange={(e) => setWFHFixedRate(e.target.checked)}
                  className="rounded"
                />
                Fixed rate ($0.70/hour)
              </label>
            </div>
          </div>
        </InlineDeductionSection>

        {/* Car Expenses Section */}
        <InlineDeductionSection
          id="car"
          title="Car Expenses"
          expanded={expandedSections.car}
          onToggle={() => toggleSection('car')}
          hasValue={cars.length > 0}
          estimatedValue={carDeductions.toFixed(2)}
        >
          <div className="space-y-4">
            {cars.map((car, index) => (
              <div key={car.id} className="p-4 bg-[#0a0b0e] border border-border rounded-lg">
                <div className="flex items-center justify-between mb-3">
                  <h5 className="font-medium text-text">Car {index + 1}</h5>
                  <button
                    onClick={() => removeCar(car.id)}
                    className="text-muted hover:text-red-400 p-1"
                    title="Remove car"
                  >
                    ×
                  </button>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Field label="Method" htmlFor={`car-method-${car.id}`} className="mb-0">
                    <select
                      id={`car-method-${car.id}`}
                      value={car.method}
                      onChange={(e) => updateCar(car.id, { method: e.target.value as 'cents_per_km' | 'logbook' })}
                      className="w-full px-3 py-2 bg-[#0f1117] border border-border rounded-lg text-text focus:ring-2 focus:ring-accent/40"
                    >
                      <option value="cents_per_km">Cents per km (88¢)</option>
                      <option value="logbook">Logbook method</option>
                    </select>
                  </Field>
                  
                  {car.method === 'cents_per_km' && (
                    <Field label="Work kilometers" htmlFor={`car-kms-${car.id}`} className="mb-0">
                      <input
                        id={`car-kms-${car.id}`}
                        type="number"
                        min="0"
                        max="25000"
                        value={car.kms || ''}
                        onChange={(e) => updateCar(car.id, { kms: parseInt(e.target.value) || undefined })}
                        placeholder="e.g., 2000"
                        className="w-full px-3 py-2 bg-[#0f1117] border border-border rounded-lg text-text focus:ring-2 focus:ring-accent/40"
                      />
                    </Field>
                  )}
                  
                  {car.method === 'logbook' && (
                    <Field label="Work use %" htmlFor={`car-pct-${car.id}`} className="mb-0">
                      <input
                        id={`car-pct-${car.id}`}
                        type="number"
                        min="0"
                        max="100"
                        value={car.work_use_pct || ''}
                        onChange={(e) => updateCar(car.id, { work_use_pct: parseFloat(e.target.value) || undefined })}
                        placeholder="e.g., 60"
                        className="w-full px-3 py-2 bg-[#0f1117] border border-border rounded-lg text-text focus:ring-2 focus:ring-accent/40"
                      />
                    </Field>
                  )}
                </div>
                
                {car.method === 'cents_per_km' && car.kms && (
                  <div className="mt-3 text-sm text-accent">
                    Estimated: ${(car.kms * 0.88).toFixed(2)} ({car.kms} km × $0.88)
                  </div>
                )}
              </div>
            ))}
            
            <button
              onClick={addCar}
              className="w-full p-3 border-2 border-dashed border-border text-muted hover:border-accent hover:text-accent transition-colors rounded-lg"
            >
              + Add Car
            </button>
          </div>
        </InlineDeductionSection>

        {/* Phone & Internet Section */}
        <InlineDeductionSection
          id="phone"
          title="Phone & Internet"
          expanded={expandedSections.phone}
          onToggle={() => toggleSection('phone')}
          hasValue={!!phone_internet_work_use_pct || phone_internet_incidental_claims}
          estimatedValue={phoneDeductions.toFixed(2)}
        >
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 text-sm text-text">
                <input
                  type="checkbox"
                  checked={phone_internet_incidental_claims}
                  onChange={(e) => setPhoneInternetIncidental(e.target.checked)}
                  className="rounded"
                />
                Incidental use only ($50 claim)
              </label>
            </div>
            
            {!phone_internet_incidental_claims && (
              <Field label="Work use percentage" htmlFor="phone-work-pct" className="mb-0">
                <input
                  id="phone-work-pct"
                  type="number"
                  min="0"
                  max="100"
                  value={phone_internet_work_use_pct || ''}
                  onChange={(e) => setPhoneInternetWorkPct(parseFloat(e.target.value) || undefined)}
                  placeholder="e.g., 20"
                  className="w-full px-3 py-2 bg-[#0a0b0e] border border-border rounded-lg text-text focus:ring-2 focus:ring-accent/40"
                />
              </Field>
            )}
            
            <div className="text-xs text-muted">
              {phone_internet_incidental_claims ? (
                "ATO allows $50 for incidental work use without records."
              ) : (
                "For detailed method, you'll need actual phone/internet bills and usage records."
              )}
            </div>
          </div>
        </InlineDeductionSection>

        {/* Other Sections - Collapsed by default */}
        <InlineDeductionSection
          id="clothing"
          title="Clothing & Laundry"
          expanded={expandedSections.clothing}
          onToggle={() => toggleSection('clothing')}
          hasValue={!!(clothing_work_only_loads || clothing_mixed_loads || clothing_purchases)}
          estimatedValue={clothingDeductions.toFixed(2)}
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Work-only laundry loads" htmlFor="clothing-work-loads" className="mb-0">
              <input
                id="clothing-work-loads"
                type="number"
                min="0"
                value={clothing_work_only_loads || ''}
                onChange={(e) => setClothingWorkOnlyLoads(parseInt(e.target.value) || undefined)}
                placeholder="e.g., 52"
                className="w-full px-3 py-2 bg-[#0a0b0e] border border-border rounded-lg text-text focus:ring-2 focus:ring-accent/40"
              />
            </Field>
            
            <Field label="Mixed laundry loads" htmlFor="clothing-mixed-loads" className="mb-0">
              <input
                id="clothing-mixed-loads"
                type="number"
                min="0"
                value={clothing_mixed_loads || ''}
                onChange={(e) => setClothingMixedLoads(parseInt(e.target.value) || undefined)}
                placeholder="e.g., 26"
                className="w-full px-3 py-2 bg-[#0a0b0e] border border-border rounded-lg text-text focus:ring-2 focus:ring-accent/40"
              />
            </Field>
            
            <Field label="Clothing purchases ($)" htmlFor="clothing-purchases" className="mb-0">
              <input
                id="clothing-purchases"
                type="number"
                min="0"
                step="0.01"
                value={clothing_purchases || ''}
                onChange={(e) => setClothingPurchases(parseFloat(e.target.value) || undefined)}
                placeholder="e.g., 200"
                className="w-full px-3 py-2 bg-[#0a0b0e] border border-border rounded-lg text-text focus:ring-2 focus:ring-accent/40"
              />
            </Field>
          </div>
          
          <div className="text-xs text-muted mt-3">
            Work-only loads: $1.00 each. Mixed loads: $0.50 each. Only claim clothing required specifically for work.
          </div>
        </InlineDeductionSection>

        <InlineDeductionSection
          id="tools"
          title="Tools & Equipment"
          expanded={expandedSections.tools}
          onToggle={() => toggleSection('tools')}
          hasValue={tools.length > 0}
          estimatedValue={toolsDeductions.toFixed(2)}
        >
          <div className="space-y-4">
            {tools.map((tool, index) => (
              <div key={index} className="p-4 bg-[#0a0b0e] border border-border rounded-lg">
                <div className="flex items-center justify-between mb-3">
                  <h5 className="font-medium text-text">Tool {index + 1}</h5>
                  <button
                    onClick={() => removeTool(index)}
                    className="text-muted hover:text-red-400 p-1"
                    title="Remove tool"
                  >
                    ×
                  </button>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Field label="Cost ($)" htmlFor={`tool-cost-${index}`} className="mb-0">
                    <input
                      id={`tool-cost-${index}`}
                      type="number"
                      min="0"
                      step="0.01"
                      value={tool.cost || ''}
                      onChange={(e) => updateTool(index, { cost: parseFloat(e.target.value) || 0 })}
                      placeholder="e.g., 150"
                      className="w-full px-3 py-2 bg-[#0f1117] border border-border rounded-lg text-text focus:ring-2 focus:ring-accent/40"
                    />
                  </Field>
                  
                  <Field label="Work use %" htmlFor={`tool-pct-${index}`} className="mb-0">
                    <input
                      id={`tool-pct-${index}`}
                      type="number"
                      min="0"
                      max="100"
                      value={tool.work_use_pct || ''}
                      onChange={(e) => updateTool(index, { work_use_pct: parseFloat(e.target.value) || 100 })}
                      placeholder="e.g., 80"
                      className="w-full px-3 py-2 bg-[#0f1117] border border-border rounded-lg text-text focus:ring-2 focus:ring-accent/40"
                    />
                  </Field>
                </div>
                
                {tool.cost && tool.work_use_pct && (
                  <div className="mt-3 text-sm">
                    <span className="text-accent">Claimable: ${(tool.cost * (tool.work_use_pct / 100)).toFixed(2)}</span>
                    {tool.cost > 300 && (
                      <span className="text-yellow-400 ml-2">(&gt;$300 may require depreciation)</span>
                    )}
                  </div>
                )}
              </div>
            ))}
            
            <button
              onClick={addTool}
              className="w-full p-3 border-2 border-dashed border-border text-muted hover:border-accent hover:text-accent transition-colors rounded-lg"
            >
              + Add Tool/Equipment
            </button>
          </div>
        </InlineDeductionSection>

        <InlineDeductionSection
          id="donations"
          title="Gifts & Donations"
          expanded={expandedSections.donations}
          onToggle={() => toggleSection('donations')}
          hasValue={!!(donations_dgr_amount || donations_bucket_amount)}
          estimatedValue={donationsDeductions.toFixed(2)}
        >
          <div className="space-y-4">
            <Field label="DGR donations ($)" htmlFor="donations-dgr" className="mb-0">
              <input
                id="donations-dgr"
                type="number"
                min="0"
                step="0.01"
                value={donations_dgr_amount || ''}
                onChange={(e) => setDonationsDGRAmount(parseFloat(e.target.value) || undefined)}
                placeholder="e.g., 100"
                className="w-full px-3 py-2 bg-[#0a0b0e] border border-border rounded-lg text-text focus:ring-2 focus:ring-accent/40"
              />
            </Field>
            
            <div className="flex items-center gap-2">
              <label className="flex items-center gap-2 text-sm text-text">
                <input
                  type="checkbox"
                  checked={donations_is_dgr_confirmed}
                  onChange={(e) => setDonationsDGRConfirmed(e.target.checked)}
                  className="rounded"
                />
                Confirmed DGR status
              </label>
            </div>
            
            <Field label="Bucket donations ($)" htmlFor="donations-bucket" className="mb-0">
              <input
                id="donations-bucket"
                type="number"
                min="0"
                max="10"
                step="0.01"
                value={donations_bucket_amount || ''}
                onChange={(e) => setDonationsBucketAmount(parseFloat(e.target.value) || undefined)}
                placeholder="e.g., 5"
                className="w-full px-3 py-2 bg-[#0a0b0e] border border-border rounded-lg text-text focus:ring-2 focus:ring-accent/40"
              />
            </Field>
            
            <div className="text-xs text-muted">
              DGR donations: Tax deductible to registered organizations (minimum $2). 
              Bucket donations: Up to $10 without receipt.
            </div>
          </div>
        </InlineDeductionSection>

        <InlineDeductionSection
          id="union"
          title="Union & Professional Fees"
          expanded={expandedSections.union}
          onToggle={() => toggleSection('union')}
          hasValue={!!union_fees}
          estimatedValue={unionDeductions.toFixed(2)}
        >
          <Field label="Annual union/professional fees ($)" htmlFor="union-fees" className="mb-0">
            <input
              id="union-fees"
              type="number"
              min="0"
              step="0.01"
              value={union_fees || ''}
              onChange={(e) => setUnionFees(parseFloat(e.target.value) || undefined)}
              placeholder="e.g., 500"
              className="w-full px-3 py-2 bg-[#0a0b0e] border border-border rounded-lg text-text focus:ring-2 focus:ring-accent/40"
            />
          </Field>
          
          <div className="text-xs text-muted mt-3">
            Include union dues, professional association fees, and licensing costs related to your work.
          </div>
        </InlineDeductionSection>

        <InlineDeductionSection
          id="tax-affairs"
          title="Tax Affairs"
          expanded={expandedSections['tax-affairs']}
          onToggle={() => toggleSection('tax-affairs')}
          hasValue={!!tax_agent_fees}
          estimatedValue={taxAgentDeductions.toFixed(2)}
        >
          <Field label="Tax agent fees ($)" htmlFor="tax-agent-fees" className="mb-0">
            <input
              id="tax-agent-fees"
              type="number"
              min="0"
              step="0.01"
              value={tax_agent_fees || ''}
              onChange={(e) => setTaxAgentFees(parseFloat(e.target.value) || undefined)}
              placeholder="e.g., 150"
              className="w-full px-3 py-2 bg-[#0a0b0e] border border-border rounded-lg text-text focus:ring-2 focus:ring-accent/40"
            />
          </Field>
          
          <div className="text-xs text-muted mt-3">
            Fees paid to tax agents, accountants, and tax return preparation services.
          </div>
        </InlineDeductionSection>

        <InlineDeductionSection
          id="super"
          title="Personal Super Contributions"
          expanded={expandedSections.super}
          onToggle={() => toggleSection('super')}
          hasValue={!!personal_super_amount}
          estimatedValue={superDeductions.toFixed(2)}
        >
          <Field label="Personal super contributions ($)" htmlFor="personal-super" className="mb-0">
            <input
              id="personal-super"
              type="number"
              min="0"
              step="0.01"
              value={personal_super_amount || ''}
              onChange={(e) => setPersonalSuperAmount(parseFloat(e.target.value) || undefined)}
              placeholder="e.g., 5000"
              className="w-full px-3 py-2 bg-[#0a0b0e] border border-border rounded-lg text-text focus:ring-2 focus:ring-accent/40"
            />
          </Field>
          
          <div className="text-xs text-muted mt-3">
            Personal (non-concessional) super contributions. May be subject to contribution caps.
            {personal_super_amount && personal_super_amount > 30000 && (
              <span className="text-yellow-400 block mt-1">
                ⚠️ Amount exceeds $30,000 concessional cap - review contribution limits
              </span>
            )}
          </div>
        </InlineDeductionSection>

        {/* Total Summary */}
        {hasAnyDeductions && (
          <div className="bg-[#0f1117] border border-border rounded-lg p-4 mt-4">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-text">Total Estimated Deductions:</span>
              <span className="font-bold text-accent text-lg">${totalDeductions.toFixed(2)}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// Inline Deduction Section Component
function InlineDeductionSection({
  id,
  title,
  expanded,
  onToggle,
  hasValue,
  estimatedValue,
  children
}: {
  id: string
  title: string
  expanded: boolean
  onToggle: () => void
  hasValue: boolean
  estimatedValue: string
  children: React.ReactNode
}) {
  return (
    <div className="border border-border rounded-lg bg-[#0f1117]">
      <button
        type="button"
        onClick={onToggle}
        className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-[#1a1d23] transition-colors rounded-lg"
      >
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="font-medium text-text">{title}</span>
            {hasValue && (
              <span className="w-2 h-2 bg-accent rounded-full"></span>
            )}
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          {hasValue && estimatedValue !== '0' && (
            <span className="text-accent font-semibold">${estimatedValue}</span>
          )}
          <svg
            className={`w-4 h-4 text-muted transition-transform ${expanded ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>
      
      {expanded && (
        <div className="px-4 pb-4 border-t border-border">
          <div className="pt-4">
            {children}
          </div>
        </div>
      )}
    </div>
  )
}