import { domains, navItems } from '../../data/marketplace'
import type { AppPage } from '../../types/marketplace'
import Icon from '../Icon'
import SidebarSection from './SidebarSection'

type SidebarProps = {
  activePage: AppPage
  onNavigate: (page: AppPage) => void
}

function Sidebar({ activePage, onNavigate }: SidebarProps) {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="brand-mark">
          <Icon icon="lucide:layers" className="brand-icon" />
        </div>
        <span className="font-display brand-name">Loom</span>
      </div>

      <nav className="sidebar-nav" aria-label="Primary">
        <div className="nav-group primary-nav">
          {navItems.map((item) => (
            <button
              className={`nav-link${activePage === item.page ? ' active' : ''}`}
              aria-disabled={!item.page}
              id={item.id}
              key={item.id}
              onClick={() => {
                if (item.page) onNavigate(item.page)
              }}
              type="button"
            >
              <Icon icon={item.icon} className="nav-icon" />
              {item.label}
            </button>
          ))}
        </div>

        <SidebarSection title="Browse by Domain">
          <div className="domain-list">
            {domains.map((domain) => (
              <a className="domain-link" href="#" id={domain.id} key={domain.id}>
                <span>
                  <Icon icon={domain.icon} className={domain.iconClass} />
                  {domain.label}
                </span>
                <strong>{domain.count}</strong>
              </a>
            ))}
          </div>
        </SidebarSection>

        <SidebarSection title="Filter by Type">
          <label className="check-row">
            <input defaultChecked type="checkbox" />
            <span>Core Agents</span>
          </label>
          <label className="check-row">
            <input defaultChecked type="checkbox" />
            <span>Community Agents</span>
          </label>
        </SidebarSection>

        <SidebarSection title="Filter by Freshness">
          <label className="check-row">
            <input name="freshness" type="radio" />
            <span>Synced within 6 hours</span>
          </label>
          <label className="check-row">
            <input name="freshness" type="radio" />
            <span>Synced within 24 hours</span>
          </label>
          <label className="check-row">
            <input defaultChecked name="freshness" type="radio" />
            <span>Any</span>
          </label>
        </SidebarSection>

        <SidebarSection title="Filter by Rating">
          <label className="check-row">
            <input name="rating" type="radio" />
            <span className="rating-label">
              4.5+ <Icon icon="lucide:star" className="icon-amber tiny-icon" />
            </span>
          </label>
          <label className="check-row">
            <input name="rating" type="radio" />
            <span className="rating-label">
              4.0+ <Icon icon="lucide:star" className="icon-amber tiny-icon" />
            </span>
          </label>
          <label className="check-row">
            <input defaultChecked name="rating" type="radio" />
            <span>Any</span>
          </label>
        </SidebarSection>
      </nav>

      <div className="user-card">
        <div className="avatar">JD</div>
        <div className="user-copy">
          <p>John Doe</p>
          <span>Pro Plan</span>
        </div>
        <button aria-label="Settings" className="settings-button" type="button">
          <Icon icon="lucide:settings" />
        </button>
      </div>
    </aside>
  )
}

export default Sidebar
