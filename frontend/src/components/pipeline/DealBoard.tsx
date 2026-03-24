import { DealColumn } from './DealColumn'

interface DealBoardProps {
  deals: any[]
  onDealMove: (dealId: string, newStage: string) => void
}

const stages = [
  'Origination',
  'NDA Signed',
  'Diligence',
  'IOI',
  'LOI',
  'Exclusivity',
  'Signing',
  'Closing',
  'Closed',
  'Dead',
]

export function DealBoard({ deals, onDealMove }: DealBoardProps) {
  const dealsByStage = stages.reduce((acc, stage) => {
    acc[stage] = deals.filter((deal) => deal.stage === stage)
    return acc
  }, {} as Record<string, any[]>)

  const stageCounts = Object.fromEntries(
    stages.map((stage) => [
      stage,
      {
        count: dealsByStage[stage].length,
        totalValue: dealsByStage[stage].reduce(
          (sum, deal) => sum + (deal.deal_value_usd || 0),
          0
        ),
      },
    ])
  )

  return (
    <div className="flex gap-4 overflow-x-auto pb-4">
      {stages.map((stage) => (
        <DealColumn
          key={stage}
          stage={stage}
          deals={dealsByStage[stage]}
          count={stageCounts[stage].count}
          totalValue={stageCounts[stage].totalValue}
          onDealMove={onDealMove}
        />
      ))}
    </div>
  )
}
