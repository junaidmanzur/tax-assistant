// DeductionsWizard.tsx
import { useEffect } from 'react'
import { useWizardState, useFeatureFlag, useDeductionsStore } from '../../store/deductionsStore'
import Button from '../common/Button'

interface DeductionsWizardProps {
  income: number
}

const WIZARD_STEPS = [
  { id: 1, title: 'Overview & Year', description: 'Confirm tax year and get started' },
  { id: 2, title: 'Working from Home', description: 'Fixed rate method for home office expenses' },
  { id: 3, title: 'Car Expenses', description: 'Work-related vehicle costs' },
  { id: 4, title: 'Phone & Internet', description: 'Work use of personal devices' },
  { id: 5, title: 'Clothing & Laundry', description: 'Protective and work-specific clothing' },
  { id: 6, title: 'Tools & Equipment', description: 'Work-related purchases' },
  { id: 7, title: 'Gifts & Donations', description: 'DGR donations and bucket collections' },
  { id: 8, title: 'Union & Professional Fees', description: 'Membership and subscription costs' },
  { id: 9, title: 'Tax Affairs', description: 'Accountant and tax agent fees' },
  { id: 10, title: 'Personal Super', description: 'Deductible super contributions' },
  { id: 11, title: 'Review & Validate', description: 'Preview your deductions' },
  { id: 12, title: 'Apply to Tax Calc', description: 'Complete your tax calculation' },
]

export default function DeductionsWizard({ income }: DeductionsWizardProps) {
  const { isOpen, currentStep, closeWizard, nextStep, previousStep } = useWizardState()
  const { enabled: featureEnabled } = useFeatureFlag()


  // Don't render if feature is disabled or wizard is closed
  if (!featureEnabled || !isOpen) {
    return null
  }

  const currentStepData = WIZARD_STEPS.find(step => step.id === currentStep)
  const isFirstStep = currentStep === 1
  const isLastStep = currentStep === WIZARD_STEPS.length

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-[#0f1117] border border-border rounded-xl w-full max-w-2xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <div>
            <h2 className="text-xl font-semibold text-text">
              Add Deductions (2024–25)
            </h2>
            <p className="text-sm text-muted mt-1">
              Step {currentStep} of {WIZARD_STEPS.length}: {currentStepData?.title}
            </p>
          </div>
          <button
            onClick={closeWizard}
            className="text-muted hover:text-text p-2"
            aria-label="Close wizard"
          >
            ✕
          </button>
        </div>

        {/* Progress indicator */}
        <div className="px-6 py-4 bg-[#0a0b0e]">
          <div className="flex items-center space-x-2">
            <div className="flex-1 bg-border rounded-full h-2">
              <div 
                className="bg-accent rounded-full h-2 transition-all duration-300"
                style={{ width: `${(currentStep / WIZARD_STEPS.length) * 100}%` }}
              />
            </div>
            <span className="text-xs text-muted">
              {Math.round((currentStep / WIZARD_STEPS.length) * 100)}%
            </span>
          </div>
        </div>

        {/* Step content */}
        <div className="p-6 flex-1 overflow-y-auto">
          <div className="mb-6">
            <h3 className="text-lg font-medium text-text mb-2">
              {currentStepData?.title}
            </h3>
            <p className="text-muted text-sm">
              {currentStepData?.description}
            </p>
          </div>

          {/* Step-specific content will be rendered here */}
          <div className="min-h-[200px]">
            {renderStepContent(currentStep, income)}
          </div>
        </div>

        {/* Navigation footer */}
        <div className="flex items-center justify-between p-6 border-t border-border">
          <div className="flex space-x-3">
            <Button
              type="button"
              onClick={previousStep}
              disabled={isFirstStep}
              className="bg-[#1a1d23] text-text border border-border hover:bg-[#2a2d33]"
            >
              ← Back
            </Button>
            <Button
              type="button"
              onClick={closeWizard}
              className="bg-[#1a1d23] text-muted border border-border hover:bg-[#2a2d33]"
            >
              Exit
            </Button>
          </div>

          <div className="flex space-x-3">
            <Button
              type="button"
              onClick={() => {
                // Skip this category - implement skip logic
                nextStep()
              }}
              className="bg-[#1a1d23] text-muted border border-border hover:bg-[#2a2d33]"
            >
              Skip this category
            </Button>
            <Button
              type="button"
              onClick={nextStep}
              disabled={isLastStep}
            >
              {isLastStep ? 'Apply' : 'Next →'}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

function renderStepContent(step: number, income: number): React.ReactNode {
  switch (step) {
    case 1:
      return <OverviewStep income={income} />
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
      return <ReviewStep />
    case 12:
      return <ApplyStep income={income} />
    default:
      return <div>Step content not found</div>
  }
}

// Step components - simplified for now
function OverviewStep({ income }: { income: number }) {
  return (
    <div className="space-y-4">
      <div className="bg-[#0a0b0e] p-4 rounded-lg border border-border">
        <h4 className="font-medium text-text mb-2">Tax Year: 2024–25</h4>
        <p className="text-muted text-sm">
          We'll help you calculate deductions for the 2024–25 financial year.
        </p>
      </div>
      <div className="bg-[#0a0b0e] p-4 rounded-lg border border-border">
        <h4 className="font-medium text-text mb-2">Your Income: ${income.toLocaleString()}</h4>
        <p className="text-muted text-sm">
          Deductions will be applied to reduce your taxable income.
        </p>
      </div>
      <div className="bg-blue-900/20 border border-blue-700/50 p-4 rounded-lg">
        <p className="text-blue-200 text-sm">
          <strong>Important:</strong> We only implement deductions with clear ATO guidance. 
          Some complex deductions may require professional advice.
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
    <div className="space-y-4">
      <div className="bg-[#0a0b0e] p-4 rounded-lg border border-border">
        <h4 className="font-medium text-text mb-3">Working from Home Expenses</h4>
        <p className="text-muted text-sm mb-4">
          The fixed rate method allows $0.70 per hour worked from home.
        </p>
        
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-text mb-2">
              Hours worked from home per year
            </label>
            <input
              type="number"
              min="0"
              max="2000"
              value={wfh_hours || ''}
              onChange={(e) => setWFHHours(parseInt(e.target.value) || undefined)}
              placeholder="e.g., 365"
              className="w-full px-3 py-2 bg-[#0f1117] border border-border rounded-lg text-text focus:ring-2 focus:ring-accent/40"
            />
          </div>
          
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="wfh-fixed-rate"
              checked={wfh_use_fixed_rate}
              onChange={(e) => setWFHFixedRate(e.target.checked)}
              className="rounded"
            />
            <label htmlFor="wfh-fixed-rate" className="text-sm text-text">
              Use fixed rate method ($0.70 per hour)
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

function CarExpensesStep() {
  return (
    <div className="space-y-4">
      <p className="text-muted">Car expenses step - implementation coming soon</p>
    </div>
  )
}

function PhoneInternetStep() {
  return (
    <div className="space-y-4">
      <p className="text-muted">Phone & internet step - implementation coming soon</p>
    </div>
  )
}

function ClothingLaundryStep() {
  return (
    <div className="space-y-4">
      <p className="text-muted">Clothing & laundry step - implementation coming soon</p>
    </div>
  )
}

function ToolsEquipmentStep() {
  return (
    <div className="space-y-4">
      <p className="text-muted">Tools & equipment step - implementation coming soon</p>
    </div>
  )
}

function DonationsStep() {
  return (
    <div className="space-y-4">
      <p className="text-muted">Donations step - implementation coming soon</p>
    </div>
  )
}

function UnionFeesStep() {
  return (
    <div className="space-y-4">
      <p className="text-muted">Union fees step - implementation coming soon</p>
    </div>
  )
}

function TaxAffairsStep() {
  return (
    <div className="space-y-4">
      <p className="text-muted">Tax affairs step - implementation coming soon</p>
    </div>
  )
}

function PersonalSuperStep() {
  return (
    <div className="space-y-4">
      <p className="text-muted">Personal super step - implementation coming soon</p>
    </div>
  )
}

function ReviewStep() {
  return (
    <div className="space-y-4">
      <p className="text-muted">Review step - implementation coming soon</p>
    </div>
  )
}

function ApplyStep({ income }: { income: number }) {
  return (
    <div className="space-y-4">
      <p className="text-muted">Apply step - implementation coming soon</p>
    </div>
  )
}