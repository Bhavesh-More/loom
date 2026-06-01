import { useState } from 'react'
import './App.css'
import BuildTeamButton from './components/marketplace/BuildTeamButton'
import TeamBuilderModal from './components/marketplace/TeamBuilderModal'
import Sidebar from './components/sidebar/Sidebar'
import MarketplacePage from './pages/MarketplacePage'
import ProjectsPage from './pages/ProjectsPage'
import type { AppPage } from './types/marketplace'

function App() {
  const [activePage, setActivePage] = useState<AppPage>('home')
  const [isTeamBuilderOpen, setIsTeamBuilderOpen] = useState(false)

  return (
    <div className="marketplace-app">
      <Sidebar activePage={activePage} onNavigate={setActivePage} />

      <main className="main-content">
        {activePage === 'projects' ? <ProjectsPage /> : <MarketplacePage />}
      </main>

      <BuildTeamButton onClick={() => setIsTeamBuilderOpen(true)} />

      <TeamBuilderModal
        isOpen={isTeamBuilderOpen}
        onClose={() => setIsTeamBuilderOpen(false)}
      />
    </div>
  )
}

export default App
