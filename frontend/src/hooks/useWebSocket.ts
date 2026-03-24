import { useEffect, useRef, useCallback } from 'react'
import { useWSStore } from '@/store/wsStore'
import { useDealStore } from '@/store/dealStore'
import { useAgentStore } from '@/store/agentStore'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/v1/ws'

export function useWebSocket(clientId: string = 'client-' + Math.random().toString(36).substr(2, 9)) {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectAttempts = useRef(0)
  const maxReconnectAttempts = 5
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  const setConnected = useWSStore((state) => state.setConnected)
  const setLastEvent = useWSStore((state) => state.setLastEvent)
  const updateDeal = useDealStore((state) => state.updateDeal)
  const moveDealStage = useDealStore((state) => state.moveDealStage)
  const addDeal = useDealStore((state) => state.addDeal)
  const startAgent = useAgentStore((state) => state.startAgent)
  const finishAgent = useAgentStore((state) => state.finishAgent)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const ws = new WebSocket(`${WS_URL}/${clientId}`)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      reconnectAttempts.current = 0
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        setLastEvent(data)

        // Handle specific event types
        switch (data.event) {
          case 'deal_stage_changed':
            moveDealStage(data.deal_id, data.to_stage)
            break
          case 'deal_created':
            addDeal(data.deal)
            break
          case 'deal_updated':
            updateDeal(data.deal_id, data.fields)
            break
          case 'agent_started':
            startAgent(data.job_id, data.agent, data.deal_id)
            break
          case 'agent_done':
            finishAgent(data.job_id)
            break
        }
      } catch {
        // Ignore parse errors
      }
    }

    ws.onclose = () => {
      setConnected(false)

      // Attempt reconnection with exponential backoff
      if (reconnectAttempts.current < maxReconnectAttempts) {
        const delay = Math.min(1000 * 2 ** reconnectAttempts.current, 30000)
        reconnectAttempts.current += 1
        reconnectTimeoutRef.current = setTimeout(connect, delay)
      }
    }

    ws.onerror = () => {
      ws.close()
    }
  }, [clientId, setConnected, setLastEvent, updateDeal, moveDealStage, addDeal, startAgent, finishAgent])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    wsRef.current?.close()
    setConnected(false)
  }, [setConnected])

  const sendMessage = useCallback((message: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    }
  }, [])

  useEffect(() => {
    connect()
    return () => disconnect()
  }, [connect, disconnect])

  const connected = useWSStore((state) => state.connected)
  const lastEvent = useWSStore((state) => state.lastEvent)

  return { connected, lastEvent, sendMessage, reconnect: connect }
}
