import { useEffect, useState } from 'react'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

import AgentCard, { type AgentCardData } from './AgentCard'
import MaterialIcon from './MaterialIcon'
import BorderGlow from './BorderGlow'
import type { MarketplaceFilter, MarketplaceSort } from '../lib/marketplace'

const INITIAL_VISIBLE_AGENTS = 12

let cachedAgents: AgentCardData[] | null = null
let agentsFetchPromise: Promise<AgentCardData[]> | null = null

async function getAgents(): Promise<AgentCardData[]> {
  if (cachedAgents) {
    return cachedAgents
  }
  if (agentsFetchPromise) {
    return agentsFetchPromise
  }
  agentsFetchPromise = (async () => {
    try {
      const response = await fetch(`${API_BASE_URL.replace(/\/$/, '')}/agents`)
      if (response.ok) {
        const data = await response.json()
        cachedAgents = data
        return data
      }
      throw new Error('Failed to fetch agents')
    } catch (e) {
      agentsFetchPromise = null
      throw e
    } finally {
      agentsFetchPromise = null
    }
  })()
  return agentsFetchPromise
}

type AgentGridProps = {
  selectedAgents: AgentCardData[]
  onAddToTeam: (agent: AgentCardData) => void
  onRemoveFromTeam: (agentName: string) => void
  activeFilter: MarketplaceFilter
  sortOption: MarketplaceSort
  searchTerm: string
}

function AgentGrid({
  selectedAgents,
  onAddToTeam,
  onRemoveFromTeam,
  activeFilter,
  sortOption,
  searchTerm,
}: AgentGridProps) {
  const [showAllAgents, setShowAllAgents] = useState(false)
  const [agents, setAgents] = useState<AgentCardData[]>(cachedAgents || [])

  useEffect(() => {
    let active = true

    async function loadAgents() {
      try {
        const data = await getAgents()
        if (active) {
          setAgents(data)
        }
      } catch (error) {
        console.error('Failed to fetch agents', error)
      }
    }

    void loadAgents()

    return () => {
      active = false
    }
  }, [])

  const normalizedSearch = searchTerm.trim().toLowerCase()

  const filteredAgents = agents.filter((agent) => {
    const matchesFilter =
      activeFilter === 'All Agents' ? true : agent.category === activeFilter

    if (!matchesFilter) {
      return false
    }

    if (!normalizedSearch) {
      return true
    }

    const searchableText = [
      agent.name,
      agent.description,
      agent.category,
      agent.type,
      ...agent.sources,
    ]
      .join(' ')
      .toLowerCase()

    return searchableText.includes(normalizedSearch)
  })

  const parseInstalls = (value: string) => {
    const normalized = value.trim().toLowerCase()
    if (normalized.endsWith('k')) {
      return Number.parseFloat(normalized) * 1000
    }
    if (normalized.endsWith('m')) {
      return Number.parseFloat(normalized) * 1000000
    }
    return Number.parseFloat(normalized) || 0
  }

  const sortedAgents = [...filteredAgents].sort((left, right) => {
    if (sortOption === 'Highest Rated') {
      return Number.parseFloat(right.rating) - Number.parseFloat(left.rating)
    }

    if (sortOption === 'Recently Synced') {
      const leftTime = left.syncedAt ? new Date(left.syncedAt).getTime() : 0
      const rightTime = right.syncedAt ? new Date(right.syncedAt).getTime() : 0
      return rightTime - leftTime
    }

    if (sortOption === 'Newest') {
      const leftTime = left.createdAt ? new Date(left.createdAt).getTime() : 0
      const rightTime = right.createdAt ? new Date(right.createdAt).getTime() : 0
      return rightTime - leftTime
    }

    return parseInstalls(right.installs) - parseInstalls(left.installs)
  })

  const visibleAgents = showAllAgents
    ? sortedAgents
    : sortedAgents.slice(0, INITIAL_VISIBLE_AGENTS)
  const remainingAgents = sortedAgents.length - visibleAgents.length
  const selectedAgentNames = new Set(selectedAgents.map((agent) => agent.name))
  const sectionTitle =
    activeFilter === 'All Agents' ? 'Popular Agents' : `${activeFilter} Agents`

  return (
    <section className="agent-section">
      <div className="agent-section__header">
        <h2>{sectionTitle}</h2>
        <span className="agent-section__summary">
          {sortedAgents.length} result{sortedAgents.length === 1 ? '' : 's'}
        </span>
      </div>

      {visibleAgents.length > 0 ? (
        <div className="agent-grid">
          {visibleAgents.map((agent) => (
            <BorderGlow
              key={agent.name}
              edgeSensitivity={78}
              glowColor="40 80 80"
              backgroundColor="#120F17"
              borderRadius={28}
              glowRadius={40}
              glowIntensity={1}
              coneSpread={25}
              animated={false}
              colors={['#c084fc', '#f472b6', '#38bdf8']}
            >
              <AgentCard
                agent={agent}
                isSelected={selectedAgentNames.has(agent.name)}
                onAddToTeam={onAddToTeam}
                onRemoveFromTeam={onRemoveFromTeam}
              />
            </BorderGlow>
          ))}
        </div>
      ) : (
        <div className="agent-empty-state">
          <MaterialIcon name="filter_alt_off" />
          <p>
            {normalizedSearch
              ? 'No agents match this search and filter.'
              : 'No agents match this filter yet.'}
          </p>
        </div>
      )}

      <div className="market-pagination">
        <span>
          Showing {visibleAgents.length} of {sortedAgents.length} agents
        </span>
        {remainingAgents > 0 ? (
          <button type="button" onClick={() => setShowAllAgents(true)}>
            Load more agents
          </button>
        ) : null}
      </div>
    </section>
  )
}

export default AgentGrid
