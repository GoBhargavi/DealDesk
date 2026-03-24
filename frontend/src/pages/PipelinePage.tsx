import { useDeals, useMoveDealStage } from '@/hooks/useDeals'
import { DealBoard } from '@/components/pipeline/DealBoard'
import { Layout } from '@/components/layout/Layout'

export function PipelinePage() {
  const { data: dealsResponse, isLoading, error } = useDeals()
  const moveDealStage = useMoveDealStage()

  if (isLoading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-full">
          <div className="text-white">Loading deals...</div>
        </div>
      </Layout>
    )
  }

  if (error) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-full">
          <div className="text-danger">Error loading deals</div>
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-white mb-2">Deal Pipeline</h1>
          <p className="text-muted">
            Manage and track M&A deals through the investment process
          </p>
        </div>

        <DealBoard
          deals={dealsResponse?.deals || []}
          onDealMove={(dealId, newStage) => {
            moveDealStage.mutate({ id: dealId, stage: newStage })
          }}
        />
      </div>
    </Layout>
  )
}
