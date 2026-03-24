import { useWSStore } from '@/store/wsStore'
import { useDealStore } from '@/store/dealStore'
import { cn } from '@/lib/utils'

interface TopBarProps {
  className?: string
}

export function TopBar({ className }: TopBarProps) {
  const connected = useWSStore((state) => state.connected)
  const deals = useDealStore((state) => state.deals)
  const selectedDealId = useDealStore((state) => state.selectedDealId)
  const setSelectedDealId = useDealStore((state) => state.setSelectedDealId)

  const selectedDeal = deals.find((d) => d.id === selectedDealId)

  return (
    <div className={cn('h-16 bg-surface border-b border-surface-light flex items-center justify-between px-6', className)}>
      {/* Page Title */}
      <div className="flex items-center gap-4">
        <h2 className="text-lg font-semibold text-white">
          {selectedDeal ? selectedDeal.name : 'Deal Pipeline'}
        </h2>
        {selectedDeal && (
          <div className="flex items-center gap-2 text-sm text-muted">
            <span>{selectedDeal.target_company}</span>
            <span>•</span>
            <span className="text-accent">{selectedDeal.sector}</span>
          </div>
        )}
      </div>

      {/* Right Section */}
      <div className="flex items-center gap-4">
        {/* Deal Selector */}
        <select
          value={selectedDealId || ''}
          onChange={(e) => setSelectedDealId(e.target.value || null)}
          className="bg-surface-light border border-surface-light rounded-md px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-accent"
        >
          <option value="">All Deals</option>
          {deals.map((deal) => (
            <option key={deal.id} value={deal.id}>
              {deal.name} ({deal.target_company})
            </option>
          ))}
        </select>

        {/* Connection Indicator */}
        <div className="flex items-center gap-2">
          <div
            className={cn(
              'w-2 h-2 rounded-full',
              connected ? 'bg-success' : 'bg-danger'
            )}
          />
          <span className="text-xs text-muted">
            {connected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>
    </div>
  )
}
