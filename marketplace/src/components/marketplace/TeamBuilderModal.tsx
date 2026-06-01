import { examples, teamSlots } from '../../data/marketplace'
import Icon from '../Icon'

type TeamBuilderModalProps = {
  isOpen: boolean
  onClose: () => void
}

function TeamBuilderModal({ isOpen, onClose }: TeamBuilderModalProps) {
  if (!isOpen) return null

  return (
    <div className="modal-backdrop" role="presentation">
      <section
        aria-labelledby="team-builder-title"
        aria-modal="true"
        className="team-modal"
        role="dialog"
      >
        <div className="modal-header">
          <div className="modal-title-row">
            <div className="modal-mark">
              <Icon icon="lucide:sparkles" />
            </div>
            <div>
              <h2 id="team-builder-title">AI Team Builder</h2>
              <p>Describe what you're building</p>
            </div>
          </div>
          <button aria-label="Close modal" className="close-button" onClick={onClose} type="button">
            <Icon icon="lucide:x" />
          </button>
        </div>

        <div className="modal-content">
          <textarea placeholder="e.g. I want to build a SaaS app with user login, Stripe subscriptions, a PostgreSQL database, and a React dashboard" />

          <div className="example-chips">
            {examples.map((example) => (
              <button key={example} type="button">
                {example}
              </button>
            ))}
          </div>

          <button className="recommend-button" type="button">
            <Icon icon="lucide:wand-2" />
            Recommend my team
          </button>

          <div className="modal-divider">
            <span></span>
            <p>Or build manually</p>
            <span></span>
          </div>

          <label className="modal-search">
            <Icon icon="lucide:search" />
            <input placeholder="Search agents to add..." type="text" />
          </label>

          <div className="team-slots">
            <p>Team Slots</p>
            <div>
              {teamSlots.map(([label, icon]) => (
                <span className="team-slot" key={label}>
                  <Icon icon={icon} />
                  {label}
                </span>
              ))}
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}

export default TeamBuilderModal
