// deductionsStore.ts - Minimal working version
import { create } from 'zustand'
import { useCallback } from 'react'
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
  
  // Copy/Template functionality
  copyToTemplate: (name: string) => void
  loadFromTemplate: (name: string) => void
  getTemplateNames: () => string[]
  deleteTemplate: (name: string) => void
  clearAllDeductions: () => void
  
  // Working from home
  setWFHHours: (hours?: number) => void
  setWFHFixedRate: (useFixedRate: boolean) => void
  
  // Car expenses
  addCar: () => string
  updateCar: (id: string, updates: Partial<CarExpense>) => void
  removeCar: (id: string) => void
  
  // Phone & internet
  setPhoneInternetWorkPct: (pct?: number) => void
  setPhoneInternetIncidental: (incidental: boolean) => void
  
  // Clothing & laundry
  setClothingWorkOnlyLoads: (loads?: number) => void
  setClothingMixedLoads: (loads?: number) => void
  setClothingPurchases: (amount?: number) => void
  
  // Tools & equipment
  addTool: () => void
  updateTool: (index: number, updates: Partial<ToolExpense>) => void
  removeTool: (index: number) => void
  
  // Donations
  setDonationsDGRAmount: (amount?: number) => void
  setDonationsBucketAmount: (amount?: number) => void
  setDonationsDGRConfirmed: (confirmed: boolean) => void
  
  // Other deductions
  setUnionFees: (amount?: number) => void
  setTaxAgentFees: (amount?: number) => void
  setPersonalSuperAmount: (amount?: number) => void
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
  
  // Car expenses
  addCar: () => {
    const newCarId = `car-${Date.now()}`
    const newCar: CarExpense = {
      id: newCarId,
      method: 'cents_per_km'
    }
    set(state => ({ cars: [...state.cars, newCar] }))
    return newCarId
  },
  
  updateCar: (id, updates) => {
    set(state => ({
      cars: state.cars.map(car => 
        car.id === id ? { ...car, ...updates } : car
      )
    }))
  },
  
  removeCar: (id) => {
    set(state => ({
      cars: state.cars.filter(car => car.id !== id)
    }))
  },
  
  // Phone & internet
  setPhoneInternetWorkPct: (phone_internet_work_use_pct) => 
    set({ phone_internet_work_use_pct }),
  setPhoneInternetIncidental: (phone_internet_incidental_claims) => 
    set({ phone_internet_incidental_claims }),
  
  // Clothing & laundry
  setClothingWorkOnlyLoads: (clothing_work_only_loads) => 
    set({ clothing_work_only_loads }),
  setClothingMixedLoads: (clothing_mixed_loads) => 
    set({ clothing_mixed_loads }),
  setClothingPurchases: (clothing_purchases) => 
    set({ clothing_purchases }),
  
  // Tools & equipment
  addTool: () => {
    const newTool: ToolExpense = { cost: 0, work_use_pct: 100 }
    set(state => ({ tools: [...state.tools, newTool] }))
  },
  
  updateTool: (index, updates) => {
    set(state => ({
      tools: state.tools.map((tool, i) => 
        i === index ? { ...tool, ...updates } : tool
      )
    }))
  },
  
  removeTool: (index) => {
    set(state => ({
      tools: state.tools.filter((_, i) => i !== index)
    }))
  },
  
  // Donations
  setDonationsDGRAmount: (donations_dgr_amount) => 
    set({ donations_dgr_amount }),
  setDonationsBucketAmount: (donations_bucket_amount) => 
    set({ donations_bucket_amount }),
  setDonationsDGRConfirmed: (donations_is_dgr_confirmed) => 
    set({ donations_is_dgr_confirmed }),
  
  // Other deductions
  setUnionFees: (union_fees) => set({ union_fees }),
  setTaxAgentFees: (tax_agent_fees) => set({ tax_agent_fees }),
  setPersonalSuperAmount: (personal_super_amount) => 
    set({ personal_super_amount }),
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
  
  // Fetch feature status from API
  const checkFeatureStatus = useCallback(async () => {
    try {
      const response = await fetch('/api/features/deductions')
      if (response.ok) {
        const data = await response.json()
        setEnabled(data.enabled)
        return data.enabled
      }
    } catch (error) {
      console.error('Failed to check feature status:', error)
    }
    return false
  }, [setEnabled])
  
  // Toggle feature flag via API
  const toggleFeature = async (newEnabled: boolean) => {
    try {
      const response = await fetch('/api/features/deductions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: newEnabled })
      })
      if (response.ok) {
        const data = await response.json()
        setEnabled(data.enabled)
        return data.enabled
      }
    } catch (error) {
      console.error('Failed to toggle feature:', error)
    }
    return enabled
  }
  
  return {
    enabled,
    setEnabled,
    checkFeatureStatus,
    toggleFeature,
  }
}