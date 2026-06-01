import { useState } from 'react'

import type { AgentCardData } from '../components/AgentCard'
import AgentGrid from '../components/AgentGrid'
import MarketplaceCategories from '../components/MarketplaceCategories'
import MarketplaceFilterBar from '../components/MarketplaceFilterBar'
import MarketplaceHero from '../components/MarketplaceHero'
import ProjectCheckoutModal from '../components/ProjectCheckoutModal'
import Sidebar, { type AppPage } from '../components/Sidebar'

type MarketplacePageProps = {
  onNavigate: (page: AppPage) => void
}

function MarketplacePage({ onNavigate }: MarketplacePageProps) {
  const [selectedAgents, setSelectedAgents] = useState<AgentCardData[]>([])
  const [isCheckoutOpen, setIsCheckoutOpen] = useState(false)

  const handleAddToTeam = (agent: AgentCardData) => {
    setSelectedAgents((currentAgents) =>
      currentAgents.some((currentAgent) => currentAgent.name === agent.name)
        ? currentAgents
        : [...currentAgents, agent],
    )
  }

  const handleRemoveFromTeam = (agentName: string) => {
    setSelectedAgents((currentAgents) =>
      currentAgents.filter((agent) => agent.name !== agentName),
    )
  }

  return (
    <div className="workspace-app">
      <Sidebar activePage="marketplace" onNavigate={onNavigate} />

      <main className="marketplace-main">
        <MarketplaceHero
          selectedAgents={selectedAgents}
          onCheckout={() => setIsCheckoutOpen(true)}
          onRemoveFromTeam={handleRemoveFromTeam}
        />
        <MarketplaceCategories />
        <MarketplaceFilterBar />
        <AgentGrid
          selectedAgents={selectedAgents}
          onAddToTeam={handleAddToTeam}
          onRemoveFromTeam={handleRemoveFromTeam}
        />
      </main>

      {isCheckoutOpen ? (
        <ProjectCheckoutModal
          agents={selectedAgents}
          onClose={() => setIsCheckoutOpen(false)}
          onRemoveAgent={handleRemoveFromTeam}
        />
      ) : null}
    </div>
  )
}

export default MarketplacePage
