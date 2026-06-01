import { useState } from 'react'
import type { AppPage } from './components/Sidebar'
import MarketplacePage from './pages/MarketplacePage'
import WorkspacePage from './pages/WorkspacePage'
import './App.css'

function App() {
  const [page, setPage] = useState<AppPage>('chat')

  if (page === 'marketplace') {
    return <MarketplacePage onNavigate={setPage} />
  }

  return <WorkspacePage activePage={page} onNavigate={setPage} />
}

export default App
