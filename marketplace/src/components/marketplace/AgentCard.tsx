import type { Agent } from '../../types/marketplace'
import Icon from '../Icon'

type AgentCardProps = {
  agent: Agent
}

function AgentCard({ agent }: AgentCardProps) {
  return (
    <article className={`agent-card${agent.type === 'Community' ? ' community' : ''}`}>
      <div className="agent-card-top">
        <div className="agent-title-row">
          <div className={agent.iconWrapClass}>
            <Icon icon={agent.icon} className={agent.iconClass} />
          </div>
          <div>
            <div className="agent-name-row">
              <h3>{agent.name}</h3>
              <span>{agent.version}</span>
            </div>
            <strong className={agent.type === 'Core' ? 'core-badge' : 'community-badge'}>
              {agent.type}
            </strong>
          </div>
        </div>
        <div className="agent-rating">
          <Icon icon="lucide:star" className="icon-amber" />
          <span>{agent.rating}</span>
        </div>
      </div>

      <p className="agent-description">{agent.description}</p>

      <div className="source-list">
        {agent.sources.map((source) => (
          <span className="source-tag" key={`${agent.id}-${source}`}>
            {source}
          </span>
        ))}
      </div>

      <div className="agent-meta">
        <span>
          <Icon icon="lucide:refresh-cw" className={agent.syncClass} />
          {agent.synced}
        </span>
        <span>
          <Icon icon="lucide:download" />
          {agent.installs}
        </span>
      </div>

      <div className="agent-actions">
        <button type="button">Add to Team</button>
        <a href="#" id={`${agent.id}-details-link`}>
          Details
        </a>
      </div>
    </article>
  )
}

export default AgentCard
