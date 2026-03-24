import { Layout } from '@/components/layout/Layout'

export function DCFPage() {
  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-white mb-2">DCF Valuation</h1>
          <p className="text-muted">
            Discounted cash flow modeling and analysis
          </p>
        </div>

        <div className="bg-surface rounded-lg border border-surface-light p-6">
          <div className="text-center text-muted">
            DCF model component coming soon...
          </div>
        </div>
      </div>
    </Layout>
  )
}
