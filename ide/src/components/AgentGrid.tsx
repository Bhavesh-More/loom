import { useState } from 'react'

import AgentCard, { type AgentCardData } from './AgentCard'
import MaterialIcon from './MaterialIcon'

const INITIAL_VISIBLE_AGENTS = 12

const agents: AgentCardData[] = [
  {
    id: '204cfaf9-aa29-430f-9309-4a97e81e7791',
    name: 'FastAPI Agent',
    version: 'v1.0.0',
    type: 'Core',
    rating: '4.8',
    icon: 'speed',
    tone: 'amber',
    description: 'Fast API routing, validation, and async service scaffolding.',
    sources: ['https://fastapi.tiangolo.com/', 'https://docs.pydantic.dev/'],
    synced: 'Synced 2h ago',
    installs: '12.4k',
  },
  {
    id: 'ee1b6b17-a05d-4e4f-a313-cdae446f62c0',
    name: 'Streamlit Agent',
    version: 'v1.0.0',
    type: 'Core',
    rating: '4.7',
    icon: 'dashboard',
    tone: 'green',
    description: 'Rapid data apps, dashboards, and internal tools in minutes.',
    sources: ['https://docs.streamlit.io/', 'https://streamlit.io/'],
    synced: 'Synced 1h ago',
    installs: '9.8k',
  },
  {
    id: 'fdcc23b6-0106-459e-8b0e-29072d34b28c',
    name: 'MongoDB Agent',
    version: 'v1.0.0',
    type: 'Core',
    rating: '4.9',
    icon: 'database',
    tone: 'blue',
    description: 'Document modeling, indexes, and aggregation pipeline helpers.',
    sources: ['https://www.mongodb.com/docs/', 'https://www.mongodb.com/atlas/database'],
    synced: 'Synced 3h ago',
    installs: '15.2k',
  },
  {
    id: 'ef209bcf-caca-43d8-9d4d-33c47af59141',
    name: 'PostgreSQL Agent',
    version: 'v1.0.0',
    type: 'Core',
    rating: '4.8',
    icon: 'storage',
    tone: 'violet',
    description: 'Schemas, joins, query tuning, and migration-friendly workflows.',
    sources: ['https://www.postgresql.org/docs/', 'https://www.postgresql.org/'],
    synced: 'Synced 2h ago',
    installs: '11.5k',
  },
  {
    id: '7f52aad5-5292-436e-a7a7-e7056f0361bd',
    name: 'Redis Agent',
    version: 'v1.0.0',
    type: 'Core',
    rating: '4.6',
    icon: 'memory',
    tone: 'sky',
    description: 'Caching, queues, and ultra-fast key value primitives.',
    sources: ['https://redis.io/docs/latest/', 'https://redis.io/'],
    synced: 'Synced 4h ago',
    installs: '7.3k',
  },
  {
    id: '8ac481f3-a4e9-4d95-b065-4726e7c1d0f8',
    name: 'Supabase Agent',
    version: 'v1.0.0',
    type: 'Core',
    rating: '4.7',
    icon: 'lock',
    tone: 'green',
    description: 'Auth, database, storage, and realtime backend workflows.',
    sources: ['https://supabase.com/docs', 'https://supabase.com/'],
    synced: 'Synced 5h ago',
    installs: '3.2k',
  },
  {
    id: 'ea173cc5-68ce-4711-9428-a09039e61e41',
    name: 'LangGraph Agent',
    version: 'v1.0.0',
    type: 'Core',
    rating: '4.6',
    icon: 'account_tree',
    tone: 'blue',
    description: 'Stateful multi-step graphs for complex LLM workflows.',
    sources: ['https://langchain-ai.github.io/langgraph/', 'https://python.langchain.com/'],
    synced: 'Synced 6h ago',
    installs: '2.1k',
  },
  {
    id: '4c38ec8e-b2b0-42c1-a78b-ded28fd14138',
    name: 'OpenAI Agent',
    version: 'v1.0.0',
    type: 'Core',
    rating: '4.9',
    icon: 'smart_toy',
    tone: 'rose',
    description: 'Prompting, tool use, and model orchestration for app workflows.',
    sources: ['https://platform.openai.com/docs', 'https://openai.com/'],
    synced: 'Synced 8h ago',
    installs: '5.6k',
  },
  {
    id: '9d4bd9f2-263e-4f88-80c0-a83cd556f9de',
    name: 'Docker Agent',
    version: 'v1.0.0',
    type: 'Core',
    rating: '4.5',
    icon: 'package',
    tone: 'sky',
    description: 'Container builds, image hygiene, and compose setups.',
    sources: ['https://docs.docker.com/', 'https://www.docker.com/'],
    synced: 'Synced 3h ago',
    installs: '8.4k',
  },
  {
    id: '00ac1046-fc5b-4c9b-a7a3-15f94545b1a2',
    name: 'GitHub Actions Agent',
    version: 'v1.0.0',
    type: 'Core',
    rating: '4.6',
    icon: 'terminal',
    tone: 'green',
    description: 'CI pipelines, automation, and release workflow helpers.',
    sources: ['https://docs.github.com/actions', 'https://github.com/features/actions'],
    synced: 'Synced 4h ago',
    installs: '6.1k',
  },
  {
    id: '4cb0bc25-7486-4fc8-823b-cb2475f0fdd5',
    name: 'Authentication Agent',
    version: 'v1.0.0',
    type: 'Core',
    rating: '4.8',
    icon: 'verified_user',
    tone: 'amber',
    description: 'Login flows, sessions, and secure access patterns.',
    sources: ['https://auth0.com/docs', 'https://clerk.com/docs'],
    synced: 'Synced 2h ago',
    installs: '13.7k',
  },
  {
    id: '99fb18b4-39b7-4b9f-848f-ec8c8e1c17b0',
    name: 'RAG Agent',
    version: 'v1.0.0',
    type: 'Core',
    rating: '4.7',
    icon: 'psychology',
    tone: 'violet',
    description: 'Retrieval, chunking, and answer-grounding workflows.',
    sources: ['https://python.langchain.com/docs/', 'https://www.pinecone.io/learn/'],
    synced: 'Synced 5h ago',
    installs: '10.2k',
  },
  {
    id: 'fb64a956-f8af-43f9-b6c8-c3b46626ee8a',
    name: 'Pytest Agent',
    version: 'v1.0.0',
    type: 'Core',
    rating: '4.4',
    icon: 'science',
    tone: 'rose',
    description: 'Test layout, fixtures, and clean Python test patterns.',
    sources: ['https://docs.pytest.org/', 'https://docs.python.org/3/'],
    synced: 'Synced 7h ago',
    installs: '5.6k',
  },
  {
    id: '1f4ddc23-02c6-4e4a-8ca9-4b09bb37f198',
    name: 'Web Scraping Agent',
    version: 'v1.0.0',
    type: 'Core',
    rating: '4.5',
    icon: 'travel_explore',
    tone: 'blue',
    description: 'Page parsing, selectors, and safe extraction workflows.',
    sources: ['https://beautiful-soup-4.readthedocs.io/', 'https://www.scrapy.org/'],
    synced: 'Synced 8h ago',
    installs: '4.9k',
  },
]

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
