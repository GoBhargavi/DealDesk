import { DealCard } from './DealCard'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { cn } from '@/lib/utils'

interface DealColumnProps {
  stage: string
  deals: any[]
  count: number
  totalValue: number
  onDealMove: (dealId: string, newStage: string) => void
}

export function DealColumn({ stage, deals, count, totalValue, onDealMove }: DealColumnProps) {
  return (
    <div className="flex-shrink-0 w-80 bg-surface rounded-lg border border-surface-light">
      {/* Header */}
      <div className="p-4 border-b border-surface-light">
        <div className="flex items-center justify-between mb-2">
          <StatusBadge status={stage} variant="deal-stage" />
          <span className="text-sm text-muted">{count} deals</span>
        </div>
        {totalValue > 0 && (
          <div className="text-sm text-white">
            Total: ${(totalValue / 1000).toFixed(1)}B
          </div>
        )}
      </div>

      {/* Deal Cards */}
      <div className="p-3 space-y-3 min-h-[400px]">
        {deals.map((deal) => (
          <DealCard
            key={deal.id}
            deal={deal}
            onMove={onDealMove}
          />
        ))}
        {deals.length === 0 && (
          <div className="text-center text-muted text-sm py-8">
            No deals in {stage}
          </div>
        )}
      </div>
    </div>
  )
}
