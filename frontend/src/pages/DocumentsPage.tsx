import { Layout } from '@/components/layout/Layout'

export function DocumentsPage() {
  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-white mb-2">Documents</h1>
          <p className="text-muted">
            Manage deal documents and data room
          </p>
        </div>

        <div className="bg-surface rounded-lg border border-surface-light p-6">
          <div className="text-center text-muted">
            Document management component coming soon...
          </div>
        </div>
      </div>
    </Layout>
  )
}
