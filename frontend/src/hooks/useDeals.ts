import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { dealsApi } from '@/api/deals'
import { useDealStore } from '@/store/dealStore'
import type { Deal, DealStage, CreateDealRequest, UpdateDealRequest } from '@/types/deal'

const DEALS_QUERY_KEY = 'deals'

export function useDeals(filters?: {
  stage?: string
  sector?: string
  deal_type?: string
}) {
  const setDeals = useDealStore((state) => state.setDeals)

  return useQuery({
    queryKey: [DEALS_QUERY_KEY, filters],
    queryFn: async () => {
      const response = await dealsApi.list(filters)
      setDeals(response.deals)
      return response
    },
  })
}

export function useCreateDeal() {
  const queryClient = useQueryClient()
  const addDeal = useDealStore((state) => state.addDeal)

  return useMutation({
    mutationFn: (data: CreateDealRequest) => dealsApi.create(data),
    onSuccess: (deal) => {
      addDeal(deal)
      queryClient.invalidateQueries({ queryKey: [DEALS_QUERY_KEY] })
    },
  })
}

export function useUpdateDeal() {
  const queryClient = useQueryClient()
  const updateDeal = useDealStore((state) => state.updateDeal)

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateDealRequest }) =>
      dealsApi.update(id, data),
    onSuccess: (deal) => {
      updateDeal(deal.id, deal)
      queryClient.invalidateQueries({ queryKey: [DEALS_QUERY_KEY] })
    },
  })
}

export function useMoveDealStage() {
  const queryClient = useQueryClient()
  const moveDealStage = useDealStore((state) => state.moveDealStage)

  return useMutation({
    mutationFn: ({ id, stage }: { id: string; stage: DealStage }) =>
      dealsApi.moveStage(id, stage),
    onSuccess: (deal) => {
      moveDealStage(deal.id, deal.stage)
      queryClient.invalidateQueries({ queryKey: [DEALS_QUERY_KEY] })
    },
  })
}

export function useDeleteDeal() {
  const queryClient = useQueryClient()
  const removeDeal = useDealStore((state) => state.removeDeal)

  return useMutation({
    mutationFn: (id: string) => dealsApi.delete(id),
    onSuccess: (_, id) => {
      removeDeal(id)
      queryClient.invalidateQueries({ queryKey: [DEALS_QUERY_KEY] })
    },
  })
}
