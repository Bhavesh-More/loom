import { useState } from 'react'

import type { AgentCardData } from '../components/AgentCard'
import AgentGrid from '../components/AgentGrid'
import MarketplaceFilterBar from '../components/MarketplaceFilterBar'
import MarketplaceHero from '../components/MarketplaceHero'
import ProjectCheckoutModal from '../components/ProjectCheckoutModal'
import MaterialIcon from '../components/MaterialIcon'
import { type AppPage } from '../components/Sidebar'
import Grainient from '@/components/Grainient'
import {
  MARKETPLACE_FILTERS,
  MARKETPLACE_SORT_OPTIONS,
  type MarketplaceFilter,
  type MarketplaceSort,
} from '../lib/marketplace'

type MarketplacePageProps = {
  onNavigate: (page: AppPage) => void
}

function MarketplacePage({ onNavigate }: MarketplacePageProps) {
  const [selectedAgents, setSelectedAgents] = useState<AgentCardData[]>([])
  const [isCheckoutOpen, setIsCheckoutOpen] = useState(false)
  const [activeFilter, setActiveFilter] = useState<MarketplaceFilter>(MARKETPLACE_FILTERS[0])
  const [sortOption, setSortOption] = useState<MarketplaceSort>(MARKETPLACE_SORT_OPTIONS[0])
  const [searchTerm, setSearchTerm] = useState('')

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
      <main className="marketplace-main">
        <button
          className="marketplace-back-button"
          onClick={() => onNavigate('chat')}
          type="button"
        >
          <MaterialIcon name="arrow_back" />
        </button>

        <div className="relative overflow-hidden">
          <div className="absolute inset-0 z-0">
            <Grainient
              color1="#FF9FFC"
              color2="#5227FF"
              color3="#B497CF"
              timeSpeed={0.25}
              colorBalance={0}
              warpStrength={1}
              warpFrequency={5}
              warpSpeed={2}
              warpAmplitude={50}
              blendAngle={0}
              blendSoftness={0.05}
              rotationAmount={500}
              noiseScale={2}
              grainAmount={0.1}
              grainScale={2}
              grainAnimated={false}
              contrast={1.5}
              gamma={1}
              saturation={1}
              centerX={0}
              centerY={0}
              zoom={0.9}
            />
          </div>

          <div className="relative z-10 bg-transparent">
            <MarketplaceHero
              searchTerm={searchTerm}
              onSearchChange={setSearchTerm}
            />
          </div>
        </div>
        <MarketplaceFilterBar
          activeFilter={activeFilter}
          sortOption={sortOption}
          onFilterChange={setActiveFilter}
          onSortChange={setSortOption}
        />
        <AgentGrid
          key={`${activeFilter}-${sortOption}-${searchTerm}`}
          selectedAgents={selectedAgents}
          onAddToTeam={handleAddToTeam}
          onRemoveFromTeam={handleRemoveFromTeam}
          activeFilter={activeFilter}
          sortOption={sortOption}
          searchTerm={searchTerm}
        />
      </main>

      {isCheckoutOpen ? (
        <ProjectCheckoutModal
          agents={selectedAgents}
          onClose={() => setIsCheckoutOpen(false)}
          onSuccess={() => {
            setIsCheckoutOpen(false)
            setSelectedAgents([])
          }}
          onRemoveAgent={handleRemoveFromTeam}
        />
      ) : null}
    </div>
  )
}

export default MarketplacePage
