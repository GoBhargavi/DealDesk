import { Layout } from '@/components/layout/Layout'

export function CompsPage() {
  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-white mb-2">Comparable Transactions</h1>
          <p className="text-muted">
            Analyze recent M&A transactions to inform valuation
          </p>
        </div>

        <div className="bg-surface rounded-lg border border-surface-light p-6">
          <div className="text-center text-muted">
            Comps analysis component coming soon...
          </div>
        </div>
      </div>
    </Layout>
  )
}
