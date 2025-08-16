// deductionsStore.ts - Minimal working version
import { create } from 'zustand'
import type { 
  CarExpense, 
  ToolExpense, 
  DeductionsRequest,
  DeductionsPreviewResponse,
  DeductionsValidationFlags 
} from '../types/tax'

export interface DeductionsState {
  // Basic info
  year: string
  
  // Working from home
  wfh_hours?: number
  wfh_use_fixed_rate: boolean
  
  // Car expenses
  cars: CarExpense[]
  
  // Phone & internet
  phone_internet_work_use_pct?: number
  phone_internet_incidental_claims: boolean
  
  // Clothing & laundry
  clothing_work_only_loads?: number
  clothing_mixed_loads?: number
  clothing_purchases?: number
  
  // Tools & equipment
  tools: ToolExpense[]
  
  // Donations
  donations_dgr_amount?: number
  donations_bucket_amount?: number
  donations_is_dgr_confirmed: boolean
  
  // Union & professional fees
  union_fees?: number
  
  // Tax agent fees
  tax_agent_fees?: number
  
  // Personal super contributions
  personal_super_amount?: number
  
  // Calculation results
  calculation_result?: DeductionsPreviewResponse
  
  // UI state
  current_step: number
  is_wizard_open: boolean
  conflicts: string[]
  warnings: string[]
  
  // Feature flag
  feature_enabled: boolean
}

interface DeductionsActions {
  // Wizard navigation
  setCurrentStep: (step: number) => void
  nextStep: () => void
  previousStep: () => void
  openWizard: (step?: number) => void
  closeWizard: () => void
  
  // Feature flag
  setFeatureEnabled: (enabled: boolean) => void
  
  // Working from home
  setWFHHours: (hours?: number) => void
  setWFHFixedRate: (useFixedRate: boolean) => void
}

type DeductionsStore = DeductionsState & DeductionsActions

const INITIAL_STATE: DeductionsState = {
  year: '2024-25',
  wfh_use_fixed_rate: true,
  cars: [],
  phone_internet_incidental_claims: false,
  tools: [],
  donations_is_dgr_confirmed: false,
  current_step: 1,
  is_wizard_open: false,
  conflicts: [],
  warnings: [],
  feature_enabled: true,
}

export const useDeductionsStore = create<DeductionsStore>((set, get) => ({
  ...INITIAL_STATE,
  
  // Wizard navigation
  setCurrentStep: (current_step) => set({ current_step }),
  
  nextStep: () => {
    const { current_step } = get()
    const maxStep = 12
    if (current_step < maxStep) {
      set({ current_step: current_step + 1 })
    }
  },
  
  previousStep: () => {
    const { current_step } = get()
    if (current_step > 1) {
      set({ current_step: current_step - 1 })
    }
  },
  
  openWizard: (step = 1) => {
    set({ is_wizard_open: true, current_step: step })
  },
  
  closeWizard: () => {
    set({ is_wizard_open: false })
  },
  
  // Feature flag
  setFeatureEnabled: (feature_enabled) => set({ feature_enabled }),
  
  // Working from home
  setWFHHours: (wfh_hours) => set({ wfh_hours }),
  setWFHFixedRate: (wfh_use_fixed_rate) => set({ wfh_use_fixed_rate }),
}))

// Simplified selector hooks with shallow comparison
export const useWizardState = () => {
  const isOpen = useDeductionsStore(state => state.is_wizard_open)
  const currentStep = useDeductionsStore(state => state.current_step)
  const openWizard = useDeductionsStore(state => state.openWizard)
  const closeWizard = useDeductionsStore(state => state.closeWizard)
  const nextStep = useDeductionsStore(state => state.nextStep)
  const previousStep = useDeductionsStore(state => state.previousStep)
  const setCurrentStep = useDeductionsStore(state => state.setCurrentStep)
  
  return {
    isOpen,
    currentStep,
    openWizard,
    closeWizard,
    nextStep,
    previousStep,
    setCurrentStep,
  }
}

export const useDeductionsData = () => {
  const wfh_hours = useDeductionsStore(state => state.wfh_hours)
  const wfh_use_fixed_rate = useDeductionsStore(state => state.wfh_use_fixed_rate)
  
  return {
    wfh_hours,
    wfh_use_fixed_rate,
    hasAnyDeductions: false, // Simplified for now
    totalEstimated: 0, // Simplified for now
  }
}

export const useFeatureFlag = () => {
  const enabled = useDeductionsStore(state => state.feature_enabled)
  const setEnabled = useDeductionsStore(state => state.setFeatureEnabled)
  
  return {
    enabled,
    setEnabled,
  }
}