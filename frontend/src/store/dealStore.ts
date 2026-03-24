import { create } from 'zustand'
import type { Deal, DealStage } from '@/types/deal'

interface DealStore {
  deals: Deal[]
  selectedDealId: string | null
  setDeals: (deals: Deal[]) => void
  updateDeal: (id: string, updates: Partial<Deal>) => void
  moveDealStage: (id: string, newStage: DealStage) => void
  setSelectedDealId: (id: string | null) => void
  addDeal: (deal: Deal) => void
  removeDeal: (id: string) => void
}

export const useDealStore = create<DealStore>((set) => ({
  deals: [],
  selectedDealId: null,

  setDeals: (deals) => set({ deals }),

  updateDeal: (id, updates) =>
    set((state) => ({
      deals: state.deals.map((deal) =>
        deal.id === id ? { ...deal, ...updates } : deal
      ),
    })),

  moveDealStage: (id, newStage) =>
    set((state) => ({
      deals: state.deals.map((deal) =>
        deal.id === id ? { ...deal, stage: newStage } : deal
      ),
    })),

  setSelectedDealId: (id) => set({ selectedDealId: id }),

  addDeal: (deal) =>
    set((state) => ({
      deals: [deal, ...state.deals],
    })),

  removeDeal: (id) =>
    set((state) => ({
      deals: state.deals.filter((deal) => deal.id !== id),
      selectedDealId: state.selectedDealId === id ? null : state.selectedDealId,
    })),
}))
