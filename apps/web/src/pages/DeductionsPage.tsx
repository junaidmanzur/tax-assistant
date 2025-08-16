// DeductionsPage.tsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useWizardState, useDeductionsStore } from '../store/deductionsStore'
import Button from '../components/common/Button'
import Field from '../components/common/Field'

const DEDUCTION_STEPS = [
  { id: 1, title: 'Basic Information', description: 'Tax year and income details' },
  { id: 2, title: 'Working from Home', description: 'Home office expenses' },
  { id: 3, title: 'Car Expenses', description: 'Work-related vehicle costs' },
  { id: 4, title: 'Phone & Internet', description: 'Work use of personal devices' },
  { id: 5, title: 'Clothing & Laundry', description: 'Work-specific clothing' },
  { id: 6, title: 'Tools & Equipment', description: 'Work-related purchases' },
  { id: 7, title: 'Gifts & Donations', description: 'Charitable donations' },
  { id: 8, title: 'Union & Professional Fees', description: 'Membership costs' },
  { id: 9, title: 'Tax Affairs', description: 'Accountant fees' },
  { id: 10, title: 'Personal Super', description: 'Super contributions' },
  { id: 11, title: 'Review & Calculate', description: 'Final review and calculation' },
]

export default function DeductionsPage() {
  const navigate = useNavigate()
  const { currentStep, setCurrentStep } = useWizardState()
  const [income, setIncome] = useState(85000)
  const [year, setYear] = useState('2024-25')

  const currentStepData = DEDUCTION_STEPS.find(step => step.id === currentStep) || DEDUCTION_STEPS[0]
  const isFirstStep = currentStep === 1
  const isLastStep = currentStep === DEDUCTION_STEPS.length

  const handleNextStep = () => {
    if (currentStep < DEDUCTION_STEPS.length) {
      setCurrentStep(currentStep + 1)
    }
  }

  const handlePrevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleStepClick = (stepId: number) => {
    setCurrentStep(stepId)
  }

  return (
    <div className="min-h-screen bg-[#0a0b0e] text-text">
      {/* Header */}
      <header className="border-b border-border bg-[#0f1117] px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-text">Tax Deductions (2024–25)</h1>
            <p className="text-muted text-sm mt-1">Step-by-step deductions calculator</p>
          </div>
          <Button 
            type="button" 
            onClick={() => navigate('/')}
            className="bg-[#1a1d23] text-text border border-border hover:bg-[#2a2d33]"
          >
            ← Back to Calculator
          </Button>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Vertical Steps Navigation */}
          <div className="lg:col-span-1">
            <div className="sticky top-8">
              <h2 className="text-lg font-semibold text-text mb-4">Steps</h2>
              <div className="space-y-2">
                {DEDUCTION_STEPS.map((step) => (
                  <button
                    key={step.id}
                    onClick={() => handleStepClick(step.id)}
                    className={`w-full text-left p-3 rounded-lg border transition-colors ${
                      step.id === currentStep
                        ? 'bg-accent/10 border-accent text-accent'
                        : step.id < currentStep
                        ? 'bg-green-900/20 border-green-700/50 text-green-200'
                        : 'bg-[#1a1d23] border-border text-muted hover:bg-[#2a2d33]'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold ${
                        step.id === currentStep
                          ? 'bg-accent text-[#05121f]'
                          : step.id < currentStep
                          ? 'bg-green-600 text-white'
                          : 'bg-border text-muted'
                      }`}>
                        {step.id < currentStep ? '✓' : step.id}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-sm">{step.title}</div>
                        <div className="text-xs opacity-70 truncate">{step.description}</div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            <div className="bg-[#0f1117] border border-border rounded-xl p-6">
              {/* Step Header */}
              <div className="mb-6">
                <h3 className="text-xl font-semibold text-text mb-2">
                  {currentStepData.title}
                </h3>
                <p className="text-muted">{currentStepData.description}</p>
              </div>

              {/* Step Content */}
              <div className="mb-8">
                {renderStepContent(currentStep, income, setIncome, year, setYear)}
              </div>

              {/* Navigation */}
              <div className="flex items-center justify-between pt-6 border-t border-border">
                <div className="flex gap-3">
                  <Button
                    type="button"
                    onClick={handlePrevStep}
                    disabled={isFirstStep}
                    className="bg-[#1a1d23] text-text border border-border hover:bg-[#2a2d33]"
                  >
                    ← Previous
                  </Button>
                </div>

                <div className="text-sm text-muted">
                  Step {currentStep} of {DEDUCTION_STEPS.length}
                </div>

                <div className="flex gap-3">
                  <Button
                    type="button"
                    onClick={handleNextStep}
                    disabled={isLastStep}
                  >
                    {isLastStep ? 'Calculate' : 'Next →'}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function renderStepContent(
  step: number, 
  income: number, 
  setIncome: (income: number) => void,
  year: string,
  setYear: (year: string) => void
): React.ReactNode {
  switch (step) {
    case 1:
      return <BasicInfoStep income={income} setIncome={setIncome} year={year} setYear={setYear} />
    case 2:
      return <WorkingFromHomeStep />
    case 3:
      return <CarExpensesStep />
    case 4:
      return <PhoneInternetStep />
    case 5:
      return <ClothingLaundryStep />
    case 6:
      return <ToolsEquipmentStep />
    case 7:
      return <DonationsStep />
    case 8:
      return <UnionFeesStep />
    case 9:
      return <TaxAffairsStep />
    case 10:
      return <PersonalSuperStep />
    case 11:
      return <ReviewStep income={income} year={year} />
    default:
      return <div>Step content not found</div>
  }
}

function BasicInfoStep({ 
  income, 
  setIncome, 
  year, 
  setYear 
}: { 
  income: number
  setIncome: (income: number) => void
  year: string
  setYear: (year: string) => void
}) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Field label="Annual Income" htmlFor="income">
          <input
            id="income"
            type="number"
            min="0"
            value={income}
            onChange={(e) => setIncome(parseInt(e.target.value) || 0)}
            placeholder="e.g., 85000"
            className="w-full px-3 py-2 bg-[#0a0b0e] border border-border rounded-lg text-text focus:ring-2 focus:ring-accent/40"
          />
        </Field>

        <Field label="Tax Year" htmlFor="year">
          <select
            id="year"
            value={year}
            onChange={(e) => setYear(e.target.value)}
            className="w-full px-3 py-2 bg-[#0a0b0e] border border-border rounded-lg text-text focus:ring-2 focus:ring-accent/40"
          >
            <option value="2024-25">2024–25</option>
            <option value="2023-24">2023–24</option>
          </select>
        </Field>
      </div>

      <div className="bg-blue-900/20 border border-blue-700/50 p-4 rounded-lg">
        <h4 className="font-medium text-blue-200 mb-2">Getting Started</h4>
        <p className="text-blue-200 text-sm">
          We'll help you calculate your tax deductions step by step. Only claim deductions for expenses 
          that are directly related to earning your income and have proper records.
        </p>
      </div>
    </div>
  )
}

function WorkingFromHomeStep() {
  const wfh_hours = useDeductionsStore(state => state.wfh_hours)
  const wfh_use_fixed_rate = useDeductionsStore(state => state.wfh_use_fixed_rate)
  const setWFHHours = useDeductionsStore(state => state.setWFHHours)
  const setWFHFixedRate = useDeductionsStore(state => state.setWFHFixedRate)

  return (
    <div className="space-y-6">
      <div className="bg-[#0a0b0e] p-4 rounded-lg border border-border">
        <h4 className="font-medium text-text mb-3">Working from Home Expenses</h4>
        <p className="text-muted text-sm mb-4">
          The fixed rate method allows $0.70 per hour worked from home and covers phone, internet, 
          electricity, heating, cooling, and depreciation of office equipment.
        </p>
        
        <div className="space-y-4">
          <Field label="Hours worked from home per year" htmlFor="wfh-hours">
            <input
              id="wfh-hours"
              type="number"
              min="0"
              max="2000"
              value={wfh_hours || ''}
              onChange={(e) => setWFHHours(parseInt(e.target.value) || undefined)}
              placeholder="e.g., 365"
              className="w-full px-3 py-2 bg-[#0f1117] border border-border rounded-lg text-text focus:ring-2 focus:ring-accent/40"
            />
          </Field>
          
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="wfh-fixed-rate"
              checked={wfh_use_fixed_rate}
              onChange={(e) => setWFHFixedRate(e.target.checked)}
              className="rounded"
            />
            <label htmlFor="wfh-fixed-rate" className="text-sm text-text">
              Use fixed rate method ($0.70 per hour) - Recommended
            </label>
          </div>
          
          {wfh_hours && wfh_use_fixed_rate && (
            <div className="bg-green-900/20 border border-green-700/50 p-3 rounded-lg">
              <p className="text-green-200 text-sm">
                <strong>Estimated deduction:</strong> ${(wfh_hours * 0.7).toFixed(2)}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// Placeholder components for other steps
function CarExpensesStep() {
  return <div className="text-muted">Car expenses step - coming soon</div>
}

function PhoneInternetStep() {
  return <div className="text-muted">Phone & internet step - coming soon</div>
}

function ClothingLaundryStep() {
  return <div className="text-muted">Clothing & laundry step - coming soon</div>
}

function ToolsEquipmentStep() {
  return <div className="text-muted">Tools & equipment step - coming soon</div>
}

function DonationsStep() {
  return <div className="text-muted">Donations step - coming soon</div>
}

function UnionFeesStep() {
  return <div className="text-muted">Union fees step - coming soon</div>
}

function TaxAffairsStep() {
  return <div className="text-muted">Tax affairs step - coming soon</div>
}

function PersonalSuperStep() {
  return <div className="text-muted">Personal super step - coming soon</div>
}

function ReviewStep({ income, year }: { income: number, year: string }) {
  return (
    <div className="space-y-4">
      <h4 className="font-medium text-text">Review Your Deductions</h4>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-[#0a0b0e] p-4 rounded-lg border border-border">
          <div className="text-sm text-muted">Income</div>
          <div className="text-lg font-semibold text-text">${income.toLocaleString()}</div>
        </div>
        <div className="bg-[#0a0b0e] p-4 rounded-lg border border-border">
          <div className="text-sm text-muted">Tax Year</div>
          <div className="text-lg font-semibold text-text">{year}</div>
        </div>
      </div>
      <div className="text-muted">Deductions summary will appear here...</div>
    </div>
  )
}