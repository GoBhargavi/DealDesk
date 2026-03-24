import { useAgentStore } from '@/store/agentStore'
import { cn } from '@/lib/utils'

export function AgentStatusPanel() {
  const runningAgents = useAgentStore((state) => state.getRunningAgents())

  if (runningAgents.length === 0) return null

  return (
    <div className="p-3 border-t border-surface-light">
      <div className="flex items-center gap-2 mb-2">
        <div className="w-2 h-2 bg-accent rounded-full animate-pulse" />
        <span className="text-xs font-medium text-accent">
          {runningAgents.length} Agent{runningAgents.length > 1 ? 's' : ''} Running
        </span>
      </div>
      <div className="space-y-1">
        {runningAgents.map((agent) => (
          <div key={agent.jobId} className="text-xs text-muted">
            <span className="capitalize">{agent.agent}</span>
            <span className="text-muted/60 ml-1">
              ({agent.dealId.slice(0, 8)}...)
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
