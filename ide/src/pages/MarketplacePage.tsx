import { useEffect, useState } from 'react'

import AgentGrid from '../components/AgentGrid'
import MarketplaceFilterBar from '../components/MarketplaceFilterBar'
import MarketplaceHero from '../components/MarketplaceHero'
import MaterialIcon from '../components/MaterialIcon'
import { type AppPage } from '../components/Sidebar'
import Grainient from '@/components/Grainient'
import {
  MARKETPLACE_FILTERS,
  MARKETPLACE_SORT_OPTIONS,
  type MarketplaceFilter,
  type MarketplaceSort,
} from '../lib/marketplace'
import { getAgents, downloadAgent, uninstallAgent, type AgentData } from '../lib/agents'

type MarketplacePageProps = {
  onNavigate: (page: AppPage, agentId?: string | null) => void
  initialSelectedAgentId?: string | null
}

function MarketplacePage({ onNavigate, initialSelectedAgentId }: MarketplacePageProps) {
  const [activeFilter, setActiveFilter] = useState<MarketplaceFilter>(MARKETPLACE_FILTERS[0])
  const [sortOption, setSortOption] = useState<MarketplaceSort>(MARKETPLACE_SORT_OPTIONS[0])
  const [searchTerm, setSearchTerm] = useState('')

  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(initialSelectedAgentId || null)
  const [agents, setAgents] = useState<AgentData[]>([])
  const [isLoading, setIsLoading] = useState(false)

  // Sync selectedAgentId when prop changes
  useEffect(() => {
    if (initialSelectedAgentId) {
      setSelectedAgentId(initialSelectedAgentId)
    }
  }, [initialSelectedAgentId])

  useEffect(() => {
    async function loadAgents() {
      try {
        const data = await getAgents()
        setAgents(data)
      } catch (err) {
        console.error('Failed to load agents in MarketplacePage', err)
      }
    }
    void loadAgents()
    
    const handleAgentsChanged = () => void loadAgents()
    window.addEventListener('agents-changed', handleAgentsChanged)
    return () => {
      window.removeEventListener('agents-changed', handleAgentsChanged)
    }
  }, [])

  const selectedAgent = agents.find(a => a.id === selectedAgentId)

  // If an agent is selected, render its details page
  if (selectedAgentId && selectedAgent) {
    const handleDownload = async () => {
      setIsLoading(true)
      try {
        await downloadAgent(selectedAgent.id)
      } catch (err) {
        console.error('Failed to download agent', err)
      } finally {
        setIsLoading(false)
      }
    }

    const handleUninstall = async () => {
      setIsLoading(true)
      try {
        await uninstallAgent(selectedAgent.id)
      } catch (err) {
        console.error('Failed to uninstall agent', err)
      } finally {
        setIsLoading(false)
      }
    }

    return (
      <div className="workspace-app">
        <main className="marketplace-main p-6 flex flex-col gap-6 text-on-surface w-full max-w-7xl mx-auto">
          {/* Back button */}
          <div className="flex items-center gap-4">
            <button
              className="marketplace-back-button flex items-center justify-center bg-[#171717] border border-[#262626] text-on-surface-variant hover:text-white rounded-xl p-2 transition-all active:scale-95 cursor-pointer"
              onClick={() => {
                setSelectedAgentId(null)
                onNavigate('marketplace', null)
              }}
              type="button"
              aria-label="Back to Marketplace"
            >
              <MaterialIcon name="arrow_back" />
            </button>
            <span className="text-[14px] text-on-surface-variant font-medium">
              Back to Marketplace
            </span>
          </div>

          {/* Premium Hero Detail Section */}
          <div className="flex flex-col md:flex-row gap-6 bg-[#171717] border border-[#262626] p-6 rounded-2xl animate-step-fade-in">
            {/* Giant Icon */}
            <div className={`market-icon market-icon--${selectedAgent.tone} !w-24 !h-24 !rounded-2xl shrink-0 flex items-center justify-center shadow-lg`}>
              <span className="material-symbols-outlined text-[48px] text-white">
                {selectedAgent.icon}
              </span>
            </div>

            {/* Info and Actions */}
            <div className="flex-1 flex flex-col justify-between gap-4">
              <div>
                <div className="flex items-center gap-3">
                  <h1 className="text-2xl font-bold text-white leading-tight">
                    {selectedAgent.name}
                  </h1>
                  <span className="bg-[#262626] text-on-surface-variant text-[11px] px-2 py-0.5 rounded-full font-mono">
                    v{selectedAgent.version}
                  </span>
                </div>
                <div className="mt-1 flex items-center gap-4 text-[12px] text-on-surface-variant">
                  <span className="flex items-center gap-1">
                    <span className="material-symbols-outlined text-[16px] text-amber-500">star</span>
                    <strong>{selectedAgent.rating}</strong>
                  </span>
                  <span>·</span>
                  <span>{selectedAgent.installs} installs</span>
                  <span>·</span>
                  <span className="bg-primary/10 text-primary px-2 py-0.5 rounded font-semibold text-[10px]">
                    {selectedAgent.type}
                  </span>
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-3">
                {selectedAgent.downloaded ? (
                  <div className="flex items-center gap-3">
                    <span className="text-[12px] text-green-500 flex items-center gap-1">
                      <span className="material-symbols-outlined text-[16px]">check_circle</span>
                      Installed in your workspace
                    </span>
                    <button
                      onClick={handleUninstall}
                      disabled={isLoading}
                      className="px-4 py-2 bg-error/10 hover:bg-error/20 text-error rounded-lg text-[13px] font-medium transition-colors cursor-pointer"
                      type="button"
                    >
                      {isLoading ? 'Uninstalling...' : 'Uninstall'}
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={handleDownload}
                    disabled={isLoading}
                    className="px-6 py-2.5 bg-primary hover:bg-primary/90 text-on-primary rounded-lg text-[13px] font-medium transition-all shadow-md active:scale-95 cursor-pointer"
                    type="button"
                  >
                    {isLoading ? 'Downloading...' : 'Download Agent'}
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Detailed Content */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-step-fade-in" style={{ animationDelay: '0.1s' }}>
            <div className="md:col-span-2 flex flex-col gap-4 bg-[#141414] border border-[#262626]/60 p-6 rounded-2xl">
              <h2 className="text-[16px] font-semibold text-white">About this Agent</h2>
              <p className="text-[14px] text-on-surface-variant leading-relaxed whitespace-pre-line">
                {selectedAgent.description}
              </p>
            </div>

            <div className="flex flex-col gap-6 bg-[#141414] border border-[#262626]/60 p-6 rounded-2xl">
              <h2 className="text-[16px] font-semibold text-white">Agent Metadata</h2>
              <div className="flex flex-col gap-4 text-[12px] text-on-surface-variant">
                <div className="flex justify-between border-b border-[#262626]/60 pb-2">
                  <span>Category</span>
                  <span className="text-white font-medium">{selectedAgent.category}</span>
                </div>
                <div className="flex justify-between border-b border-[#262626]/60 pb-2">
                  <span>Source Type</span>
                  <span className="text-white font-medium">{selectedAgent.type}</span>
                </div>
                <div className="flex justify-between border-b border-[#262626]/60 pb-2">
                  <span>Last Synced</span>
                  <span className="text-white font-medium">{selectedAgent.synced}</span>
                </div>
                <div className="flex flex-col gap-2">
                  <span>Source Repositories</span>
                  <div className="flex flex-wrap gap-2">
                    {selectedAgent.sources.map(source => (
                      <span key={source} className="bg-[#262626] text-white px-2.5 py-1 rounded text-[11px] font-mono">
                        {source}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
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
          activeFilter={activeFilter}
          sortOption={sortOption}
          searchTerm={searchTerm}
        />
      </main>
    </div>
  )
}

export default MarketplacePage
