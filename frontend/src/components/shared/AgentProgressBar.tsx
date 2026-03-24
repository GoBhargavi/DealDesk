import { cn } from '@/lib/utils'

interface AgentProgressBarProps {
  steps: string[]
  currentStep: number
  done: boolean
  className?: string
}

export function AgentProgressBar({ steps, currentStep, done, className }: AgentProgressBarProps) {
  return (
    <div className={cn('w-full', className)}>
      <div className="flex items-center justify-between mb-2">
        {steps.map((step, index) => (
          <div key={step} className="flex items-center">
            <div
              className={cn(
                'w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium border-2',
                index < currentStep || done
                  ? 'bg-accent border-accent text-white'
                  : index === currentStep
                  ? 'border-accent text-accent bg-transparent'
                  : 'border-surface-light text-muted bg-transparent'
              )}
            >
              {index < currentStep || done ? '✓' : index + 1}
            </div>
            {index < steps.length - 1 && (
              <div
                className={cn(
                  'flex-1 h-0.5 mx-2',
                  index < currentStep || done ? 'bg-accent' : 'bg-surface-light'
                )}
              />
            )}
          </div>
        ))}
      </div>
      <div className="text-center">
        <p className="text-sm text-muted">
          {done ? 'Complete' : steps[currentStep]}
        </p>
      </div>
    </div>
  )
}
