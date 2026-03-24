import { create } from 'zustand'

interface AgentRun {
  jobId: string
  agent: string
  dealId: string
  status: 'running' | 'completed' | 'error'
  error?: string
  startedAt: Date
}

interface AgentStore {
  runningAgents: Record<string, AgentRun>
  startAgent: (jobId: string, agent: string, dealId: string) => void
  finishAgent: (jobId: string) => void
  setAgentError: (jobId: string, error: string) => void
  getRunningCount: () => number
  getRunningAgents: () => AgentRun[]
}

export const useAgentStore = create<AgentStore>((set, get) => ({
  runningAgents: {},

  startAgent: (jobId, agent, dealId) =>
    set((state) => ({
      runningAgents: {
        ...state.runningAgents,
        [jobId]: {
          jobId,
          agent,
          dealId,
          status: 'running',
          startedAt: new Date(),
        },
      },
    })),

  finishAgent: (jobId) =>
    set((state) => {
      const { [jobId]: _, ...rest } = state.runningAgents
      return { runningAgents: rest }
    }),

  setAgentError: (jobId, error) =>
    set((state) => ({
      runningAgents: {
        ...state.runningAgents,
        [jobId]: {
          ...state.runningAgents[jobId],
          status: 'error',
          error,
        },
      },
    })),

  getRunningCount: () => Object.keys(get().runningAgents).length,

  getRunningAgents: () => Object.values(get().runningAgents),
}))
