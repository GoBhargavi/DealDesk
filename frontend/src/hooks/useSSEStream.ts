import { useState, useCallback, useRef } from 'react'

interface SSEEvent {
  event: string
  data: unknown
}

interface UseSSEStreamResult {
  events: SSEEvent[]
  isStreaming: boolean
  error: string | null
  startStream: (url: string, body?: object) => void
  cancelStream: () => void
  lastEvent: SSEEvent | null
}

export function useSSEStream(): UseSSEStreamResult {
  const [events, setEvents] = useState<SSEEvent[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastEvent, setLastEvent] = useState<SSEEvent | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  const startStream = useCallback((url: string, body?: object) => {
    // Cancel any existing stream
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }

    // Reset state
    setEvents([])
    setError(null)
    setIsStreaming(true)
    setLastEvent(null)

    const controller = new AbortController()
    abortControllerRef.current = controller

    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const reader = response.body?.getReader()
        if (!reader) {
          throw new Error('Response body is not readable')
        }

        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })

          // Process complete SSE events
          const lines = buffer.split('\n\n')
          buffer = lines.pop() || ''

          for (const eventBlock of lines) {
            const lines = eventBlock.split('\n')
            let eventName = 'message'
            let eventData = ''

            for (const line of lines) {
              if (line.startsWith('event:')) {
                eventName = line.slice(6).trim()
              } else if (line.startsWith('data:')) {
                eventData = line.slice(5).trim()
              }
            }

            if (eventData) {
              try {
                const parsedData = JSON.parse(eventData)
                const sseEvent: SSEEvent = { event: eventName, data: parsedData }
                setEvents((prev) => [...prev, sseEvent])
                setLastEvent(sseEvent)

                if (eventName === 'done' || eventName === 'error') {
                  setIsStreaming(false)
                }
              } catch {
                // Ignore parse errors for malformed events
              }
            }
          }
        }
      })
      .catch((err) => {
        if (err.name !== 'AbortError') {
          setError(err.message)
          setIsStreaming(false)
        }
      })
  }, [])

  const cancelStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
    setIsStreaming(false)
  }, [])

  return {
    events,
    isStreaming,
    error,
    startStream,
    cancelStream,
    lastEvent,
  }
}
