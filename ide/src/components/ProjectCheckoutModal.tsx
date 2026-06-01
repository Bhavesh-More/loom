import { useState } from 'react'

import type { AgentCardData } from './AgentCard'
import MaterialIcon from './MaterialIcon'

type ProjectCheckoutModalProps = {
  agents: AgentCardData[]
  onClose: () => void
  onRemoveAgent: (agentName: string) => void
}

function ProjectCheckoutModal({
  agents,
  onClose,
  onRemoveAgent,
}: ProjectCheckoutModalProps) {
  const [projectPath, setProjectPath] = useState('')

  return (
    <div className="checkout-modal" role="presentation">
      <div className="checkout-modal__panel" role="dialog" aria-modal="true" aria-labelledby="checkout-title">
        <div className="checkout-modal__header">
          <div>
            <p className="label-text">Project Checkout</p>
            <h2 id="checkout-title">Create a new project</h2>
          </div>
          <button type="button" aria-label="Close checkout" onClick={onClose}>
            <MaterialIcon name="close" />
          </button>
        </div>

        <div className="checkout-modal__team">
          {agents.map((agent) => (
            <button
              aria-label={`Remove ${agent.name}`}
              key={agent.name}
              onClick={() => onRemoveAgent(agent.name)}
              type="button"
            >
              <MaterialIcon name="close" />
              <span>{agent.name}</span>
            </button>
          ))}
        </div>

        <form className="checkout-form">
          <label>
            <span>Project name</span>
            <input type="text" placeholder="Customer support automation" />
          </label>

          <label>
            <span>Project description</span>
            <textarea
              rows={10}
              placeholder="Describe what this agent team should build, automate, or maintain."
            />
          </label>

          <label>
            <span>GitHub repository</span>
            <input
              type="text"
              value={projectPath}
              placeholder="Enter GitHub repo to continue"
              onChange={(event) => setProjectPath(event.target.value)}
            />
          </label>

          <div className="checkout-form__actions">
            <button type="button" onClick={onClose}>
              Cancel
            </button>
            <button type="button">Create Project</button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default ProjectCheckoutModal
