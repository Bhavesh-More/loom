import type { AgentCardData } from './AgentCard'
import MaterialIcon from './MaterialIcon'

type MarketplaceCartProps = {
  agents: AgentCardData[]
  onCheckout: () => void
  onRemove: (agentName: string) => void
}

function MarketplaceCart({ agents, onCheckout, onRemove }: MarketplaceCartProps) {
  return (
    <aside className="team-cart" aria-label="Agent team cart">
      <div className="team-cart__header">
        <div>
          <p className="label-text">Agent Team</p>
          <h2>{agents.length} selected</h2>
        </div>
        <div className="team-cart__icon">
          <MaterialIcon name="shopping_cart" />
        </div>
      </div>

      <div className="team-cart__items">
        {agents.length === 0 ? (
          <p className="team-cart__empty">
            Add agents from the marketplace to assemble a project team.
          </p>
        ) : (
          agents.map((agent) => (
            <div className="team-cart__item" key={agent.name}>
              <div className={`market-icon market-icon--${agent.tone}`}>
                <MaterialIcon name={agent.icon} />
              </div>
              <div>
                <strong>{agent.name}</strong>
                <span>{agent.type}</span>
              </div>
              <button
                type="button"
                aria-label={`Remove ${agent.name}`}
                onClick={() => onRemove(agent.name)}
              >
                <MaterialIcon name="close" />
              </button>
            </div>
          ))
        )}
      </div>

      <button
        className="team-cart__checkout"
        disabled={agents.length === 0}
        type="button"
        onClick={onCheckout}
      >
        Checkout
      </button>
    </aside>
  )
}

export default MarketplaceCart
