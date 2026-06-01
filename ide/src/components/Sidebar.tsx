import MaterialIcon from './MaterialIcon'

export type AppPage = 'workspace' | 'marketplace'

type SidebarProps = {
  activePage: AppPage
  onNavigate: (page: AppPage) => void
}

const primaryNav = [
  { label: 'New project', icon: 'add_box', page: 'workspace' as const },
  { label: 'Marketplace', icon: 'search', page: 'marketplace' as const },
]

const projects = [{ label: 'foxy', icon: 'folder_open' }]

function Sidebar({ activePage, onNavigate }: SidebarProps) {
  return (
    <aside className="sidebar" aria-label="Workspace navigation">
      <div className="sidebar__header">
        <div>
          <p className="sidebar__brand">L00m</p>
          <p className="label-text sidebar__caption">Developer Workspace</p>
        </div>
      </div>

      <nav className="sidebar__nav">
        {primaryNav.map((item) => (
          <button
            aria-current={activePage === item.page ? 'page' : undefined}
            className={`sidebar-link${activePage === item.page ? ' sidebar-link--active' : ''}`}
            key={item.label}
            onClick={() => onNavigate(item.page)}
            type="button"
          >
            <MaterialIcon name={item.icon} />
            <span>{item.label}</span>
          </button>
        ))}

        <div className="sidebar-section">
          <p className="label-text sidebar-section__title">Projects</p>
          {projects.map((project) => (
            <a className="sidebar-link" href="#" key={project.label}>
              <MaterialIcon name={project.icon} />
              <span>{project.label}</span>
            </a>
          ))}
        </div>

        <div className="sidebar-section">
          <p className="label-text sidebar-section__title">Chats</p>
        </div>
      </nav>

      <div className="sidebar__footer">
        <a className="sidebar-link" href="#">
          <MaterialIcon name="settings" />
          <span>Settings</span>
        </a>
      </div>
    </aside>
  )
}

export default Sidebar
