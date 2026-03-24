import { cn } from '@/lib/utils'

interface StreamingTextProps {
  text: string
  isStreaming: boolean
  className?: string
}

export function StreamingText({ text, isStreaming, className }: StreamingTextProps) {
  return (
    <div className={cn('font-mono text-sm', className)}>
      {text}
      {isStreaming && (
        <span className="inline-block w-2 h-4 bg-accent ml-1 animate-pulse" />
      )}
    </div>
  )
}
