import { format } from 'date-fns'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { cn } from '@/lib/utils'

interface DealCardProps {
  deal: any
  onMove: (dealId: string, newStage: string) => void
}

export function DealCard({ deal, onMove }: DealCardProps) {
  const daysInStage = deal.created_at
    ? Math.floor((Date.now() - new Date(deal.created_at).getTime()) / (1000 * 60 * 60 * 24))
    : 0

  return (
    <div className="bg-background rounded-lg border border-surface-light p-4 hover:border-accent/50 transition-colors cursor-pointer">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="font-semibold text-white text-sm">{deal.name}</h3>
          <p className="text-xs text-muted">{deal.target_company}</p>
        </div>
        <StatusBadge status={deal.stage} variant="deal-stage" />
      </div>

      {/* Deal Value */}
      {deal.deal_value_usd && (
        <div className="text-sm font-medium text-white mb-2">
          ${(deal.deal_value_usd / 1000).toFixed(1)}B
        </div>
      )}

      {/* Details */}
      <div className="space-y-2 text-xs">
        <div className="flex items-center justify-between">
          <span className="text-muted">Sector:</span>
          <span className="text-accent">{deal.sector}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-muted">Lead:</span>
          <span>{deal.lead_banker}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-muted">Days in stage:</span>
          <span className={cn(
            daysInStage > 30 ? 'text-warning' : 'text-muted'
          )}>
            {daysInStage}
          </span>
        </div>
      </div>

      {/* Footer */}
      <div className="mt-3 pt-3 border-t border-surface-light flex items-center justify-between">
        <span className="text-xs text-muted">
          {deal.expected_close_date
            ? format(new Date(deal.expected_close_date), 'MMM d, yyyy')
            : 'No close date'}
        </span>
        <StatusBadge status={deal.deal_type} variant="deal-stage" />
      </div>
    </div>
  )
}
