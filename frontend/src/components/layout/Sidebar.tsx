import { Link, useLocation } from 'react-router-dom'
import {
  KanbanSquare,
  BarChart2,
  Calculator,
  FileText,
  Newspaper,
  FolderOpen,
  Settings,
  Users,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { AgentStatusPanel } from '@/components/shared/AgentStatusPanel'

interface SidebarProps {
  className?: string
}

const navItems = [
  { href: '/pipeline', label: 'Pipeline', icon: KanbanSquare },
  { href: '/comps', label: 'Comps Analysis', icon: BarChart2 },
  { href: '/dcf', label: 'DCF Model', icon: Calculator },
  { href: '/pitchbook', label: 'Pitch Book', icon: FileText },
  { href: '/news', label: 'News & Intelligence', icon: Newspaper },
  { href: '/documents', label: 'Documents', icon: FolderOpen },
]

export function Sidebar({ className }: SidebarProps) {
  const location = useLocation()

  return (
    <div className={cn('w-56 bg-surface border-r border-surface-light flex flex-col', className)}>
      {/* Logo */}
      <div className="p-4 border-b border-surface-light">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-accent rounded-lg flex items-center justify-center">
            <FileText className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-lg font-semibold text-white">DealDesk</h1>
        </div>
        <p className="text-xs text-muted mt-1">M&A Intelligence Platform</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-2">
        <ul className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname === item.href

            return (
              <li key={item.href}>
                <Link
                  to={item.href}
                  className={cn(
                    'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-accent text-white'
                      : 'text-muted hover:text-white hover:bg-surface-light'
                  )}
                >
                  <Icon className="w-4 h-4" />
                  {item.label}
                </Link>
              </li>
            )
          })}
        </ul>
      </nav>

      {/* Bottom Section */}
      <div className="border-t border-surface-light">
        <AgentStatusPanel />
        <div className="p-2">
          <Link
            to="/settings"
            className={cn(
              'w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors',
              location.pathname === '/settings'
                ? 'bg-accent text-white'
                : 'text-muted hover:text-white hover:bg-surface-light'
            )}
          >
            <Settings className="w-4 h-4" />
            Settings
          </Link>
        </div>
      </div>
    </div>
  )
}
