import { agents } from '../../data/marketplace'
import Icon from '../Icon'
import AgentCard from './AgentCard'

function AgentGrid() {
  return (
    <section className="agent-section">
      <div className="section-heading">
        <h2>Popular Agents</h2>
        <a href="#" id="view-all-link">
          View all
          <Icon icon="lucide:arrow-right" />
        </a>
      </div>

      <div className="agent-grid">
        {agents.map((agent) => (
          <AgentCard agent={agent} key={agent.id} />
        ))}
      </div>

      <div className="pagination">
        <span>Showing 8 of 24 agents</span>
        <button type="button">Load more agents</button>
      </div>
    </section>
  )
}

export default AgentGrid
