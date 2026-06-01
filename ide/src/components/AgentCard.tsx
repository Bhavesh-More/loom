import MaterialIcon from './MaterialIcon'

export type AgentCardData = {
  name: string
  version: string
  type: 'Core' | 'Community'
  rating: string
  icon: string
  tone: 'amber' | 'green' | 'blue' | 'violet' | 'sky' | 'rose'
  description: string
  sources: string[]
  synced: string
  installs: string
}

type AgentCardProps = {
  agent: AgentCardData
  isSelected: boolean
  onAddToTeam: (agent: AgentCardData) => void
  onRemoveFromTeam: (agentName: string) => void
}

function AgentCard({
  agent,
  isSelected,
  onAddToTeam,
  onRemoveFromTeam,
}: AgentCardProps) {
  return (
    <article
      className={`agent-card${agent.type === 'Community' ? ' agent-card--community' : ''}${
        isSelected ? ' agent-card--selected' : ''
      }`}
    >
      <div className="agent-card__header">
        <div className="agent-card__identity">
          <div className={`market-icon market-icon--${agent.tone}`}>
            <MaterialIcon name={agent.icon} />
          </div>
          <div>
            <div className="agent-card__title-row">
              <h3>{agent.name}</h3>
              <span>{agent.version}</span>
            </div>
            <strong>{agent.type}</strong>
          </div>
        </div>

        <div className="agent-card__rating">
          <MaterialIcon name="star" />
          <span>{agent.rating}</span>
        </div>
      </div>

      <p className="agent-card__description">{agent.description}</p>

      <div className="agent-card__sources">
        {agent.sources.map((source) => (
          <button type="button" key={source}>
            {source}
          </button>
        ))}
      </div>

      <div className="agent-card__meta">
        <span>
          <MaterialIcon name="sync" /> {agent.synced}
        </span>
        <span>
          <MaterialIcon name="download" /> {agent.installs} installs
        </span>
      </div>

      <div className="agent-card__actions">
        <button
          className={isSelected ? 'agent-card__team-button--selected' : undefined}
          type="button"
          onClick={() =>
            isSelected ? onRemoveFromTeam(agent.name) : onAddToTeam(agent)
          }
        >
          <span className="agent-card__team-label">
            {isSelected ? 'In Team' : 'Add to Team'}
          </span>
          {isSelected ? (
            <span className="agent-card__team-remove-label">Remove from Team</span>
          ) : null}
        </button>
        <a href="#">Details</a>
      </div>
    </article>
  )
}

export default AgentCard
