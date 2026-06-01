import { heroAgents } from '../../data/marketplace'
import Icon from '../Icon'

function Hero() {
  return (
    <section className="hero-section">
      <div className="hero-content">
        <div className="hero-copy">
          <h1>Discover the world's top AI coding agents</h1>
          <p>
            Build faster with pre-trained agents that know your stack. Fresh
            knowledge, zero hallucinations.
          </p>
          <label className="search-box">
            <Icon icon="lucide:search" />
            <input
              placeholder="Search agents by name, specialty, or library..."
              type="text"
            />
          </label>
        </div>
      </div>

      <div className="floating-agents" aria-hidden="true">
        {heroAgents.map((agent) => (
          <div className="floating-agent-card" key={agent.name}>
            <div className="floating-agent-row">
              <div className={`floating-agent-icon ${agent.wrapClass}`}>
                <Icon icon={agent.icon} className={agent.iconClass} />
              </div>
              <div>
                <p>{agent.name}</p>
                <span>
                  {agent.stat.split(' Â· ')[0]}
                  <Icon icon="lucide:star" className="icon-amber" />Â·{' '}
                  {agent.stat.split(' Â· ')[1]}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}

export default Hero
