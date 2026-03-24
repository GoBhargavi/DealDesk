import { cn } from '@/lib/utils'

type StatusVariant = 'deal-stage' | 'sentiment' | 'severity' | 'doc-status'

interface StatusBadgeProps {
  status: string
  variant?: StatusVariant
  className?: string
}

const statusStyles: Record<StatusVariant, Record<string, string>> = {
  'deal-stage': {
    'Origination': 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    'NDA Signed': 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
    'Diligence': 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    'IOI': 'bg-orange-500/20 text-orange-400 border-orange-500/30',
    'LOI': 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    'Exclusivity': 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    'Signing': 'bg-pink-500/20 text-pink-400 border-pink-500/30',
    'Closing': 'bg-teal-500/20 text-teal-400 border-teal-500/30',
    'Closed': 'bg-green-500/20 text-green-400 border-green-500/30',
    'Dead': 'bg-red-500/20 text-red-400 border-red-500/30',
  },
  'sentiment': {
    'positive': 'bg-green-500/20 text-green-400 border-green-500/30',
    'neutral': 'bg-gray-500/20 text-gray-400 border-gray-500/30',
    'negative': 'bg-red-500/20 text-red-400 border-red-500/30',
  },
  'severity': {
    'High': 'bg-red-500/20 text-red-400 border-red-500/30',
    'Medium': 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    'Low': 'bg-green-500/20 text-green-400 border-green-500/30',
  },
  'doc-status': {
    'Uploading': 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    'Processing': 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    'Ready': 'bg-green-500/20 text-green-400 border-green-500/30',
    'Error': 'bg-red-500/20 text-red-400 border-red-500/30',
  },
}

export function StatusBadge({ status, variant = 'deal-stage', className }: StatusBadgeProps) {
  const style = statusStyles[variant]?.[status] || 'bg-gray-500/20 text-gray-400 border-gray-500/30'

  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border',
        style,
        className
      )}
    >
      {status}
    </span>
  )
}
