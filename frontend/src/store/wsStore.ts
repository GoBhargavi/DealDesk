import { create } from 'zustand'

interface WSEvent {
  event: string
  [key: string]: unknown
}

interface WSStore {
  connected: boolean
  lastEvent: WSEvent | null
  setConnected: (connected: boolean) => void
  setLastEvent: (event: WSEvent) => void
}

export const useWSStore = create<WSStore>((set) => ({
  connected: false,
  lastEvent: null,

  setConnected: (connected) => set({ connected }),

  setLastEvent: (event) => set({ lastEvent: event }),
}))
