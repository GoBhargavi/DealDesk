import { Layout } from '@/components/layout/Layout'

export function NewsPage() {
  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-white mb-2">News & Intelligence</h1>
          <p className="text-muted">
            Market news and deal-specific intelligence
          </p>
        </div>

        <div className="bg-surface rounded-lg border border-surface-light p-6">
          <div className="text-center text-muted">
            News feed component coming soon...
          </div>
        </div>
      </div>
    </Layout>
  )
}
