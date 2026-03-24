import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import { useWebSocket } from '@/hooks/useWebSocket'
import { PipelinePage } from '@/pages/PipelinePage'
import { CompsPage } from '@/pages/CompsPage'
import { DCFPage } from '@/pages/DCFPage'
import { PitchbookPage } from '@/pages/PitchbookPage'
import { NewsPage } from '@/pages/NewsPage'
import { DocumentsPage } from '@/pages/DocumentsPage'
import '@/index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 1,
    },
  },
})

function App() {
  // Initialize WebSocket connection
  useWebSocket()

  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="min-h-screen bg-background">
          <Routes>
            <Route path="/" element={<PipelinePage />} />
            <Route path="/pipeline" element={<PipelinePage />} />
            <Route path="/comps" element={<CompsPage />} />
            <Route path="/dcf" element={<DCFPage />} />
            <Route path="/pitchbook" element={<PitchbookPage />} />
            <Route path="/news" element={<NewsPage />} />
            <Route path="/documents" element={<DocumentsPage />} />
          </Routes>
        </div>
      </Router>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#1E293B',
            color: '#ffffff',
            border: '1px solid #334155',
          },
          success: {
            iconTheme: {
              primary: '#10B981',
              secondary: '#ffffff',
            },
          },
          error: {
            iconTheme: {
              primary: '#EF4444',
              secondary: '#ffffff',
            },
          },
        }}
      />
    </QueryClientProvider>
  )
}

export default App
