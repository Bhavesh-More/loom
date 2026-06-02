import { useEffect, useState } from 'react'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

import AgentCard, { type AgentCardData } from './AgentCard'
import MaterialIcon from './MaterialIcon'

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
}

function AgentGrid({
  selectedAgents,
  onAddToTeam,
  onRemoveFromTeam,
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

  const visibleAgents = showAllAgents ? agents : agents.slice(0, INITIAL_VISIBLE_AGENTS)
  const remainingAgents = agents.length - visibleAgents.length
  const selectedAgentNames = new Set(selectedAgents.map((agent) => agent.name))

  return (
    <section className="agent-section">
      <div className="agent-section__header">
        <h2>Popular Agents</h2>
        <a href="#">
          View all <MaterialIcon name="arrow_forward" />
        </a>
      </div>

      <div className="agent-grid">
        {visibleAgents.map((agent) => (
          <AgentCard
            agent={agent}
            isSelected={selectedAgentNames.has(agent.name)}
            key={agent.name}
            onAddToTeam={onAddToTeam}
            onRemoveFromTeam={onRemoveFromTeam}
          />
        ))}
      </div>

      <div className="market-pagination">
        <span>
          Showing {visibleAgents.length} of {agents.length} agents
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
