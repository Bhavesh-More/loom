import { useEffect, useState } from 'react'
import MaterialIcon from './MaterialIcon'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export type AppPage = 'chat' | 'marketplace'

type SidebarProps = {
  activePage: AppPage
  onNavigate: (page: AppPage) => void
}

const primaryNav = [
  { label: 'New chat', icon: 'add_box', page: 'chat' as const },
  { label: 'Marketplace', icon: 'search', page: 'marketplace' as const },
]

type Project = {
  id: string
  name: string
}

let cachedProjects: Project[] | null = null
let projectsFetchPromise: Promise<Project[]> | null = null

async function getProjects(): Promise<Project[]> {
  if (cachedProjects) {
    return cachedProjects
  }
  if (projectsFetchPromise) {
    return projectsFetchPromise
  }
  projectsFetchPromise = (async () => {
    try {
      const response = await fetch(`${API_BASE_URL.replace(/\/$/, '')}/projects/get-projects`, {
        method: 'POST',
      })
      if (response.ok) {
        const data = await response.json()
        cachedProjects = data
        return data
      }
      throw new Error('Failed to fetch projects')
    } catch (e) {
      projectsFetchPromise = null
      throw e
    } finally {
      projectsFetchPromise = null
    }
  })()
  return projectsFetchPromise
}

function Sidebar({ activePage, onNavigate }: SidebarProps) {
  const [projects, setProjects] = useState<Project[]>([])

  useEffect(() => {
    let active = true

    async function loadProjects(force = false) {
      if (force) {
        cachedProjects = null
      }
      try {
        const data = await getProjects()
        if (active) {
          setProjects(data)
        }
      } catch (error) {
        console.error('Failed to fetch projects', error)
      }
    }

    void loadProjects()

    const handleProjectCreated = () => {
      void loadProjects(true)
    }

    window.addEventListener('project-created', handleProjectCreated)

    return () => {
      active = false
      window.removeEventListener('project-created', handleProjectCreated)
    }
  }, [])

  return (
    <aside className="sidebar" aria-label="Workspace navigation">
      <div className="sidebar__header">
        <div>
          <p className="sidebar__brand">L00m</p>
          <p className="label-text sidebar__caption">Developer Workspace</p>
        </div>
      </div>

      <nav className="sidebar__nav">
        {activePage === 'marketplace' ? (
          <button
            className="sidebar-link"
            onClick={() => onNavigate('chat')}
            type="button"
          >
            <MaterialIcon name="arrow_back" />
            <span>Back</span>
          </button>
        ) : (
          <>
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
                <a className="sidebar-link" href="#" key={project.id}>
                  <MaterialIcon name="folder_open" />
                  <span>{project.name}</span>
                </a>
              ))}
            </div>

            <div className="sidebar-section">
              <p className="label-text sidebar-section__title">Chats</p>
            </div>
          </>
        )}
      </nav>

      <div className="sidebar__footer">
        <a className="sidebar-link" href="#">
          <MaterialIcon name="info" />
          <span>Support</span>
        </a>

        <a className="sidebar-link" href="#">
          <MaterialIcon name="book" />
          <span>Documentation</span>
        </a>

        <a className="sidebar-link" href="#">
          <MaterialIcon name="settings" />
          <span>Settings</span>
        </a>
      </div>
    </aside>
  )
}

export default Sidebar
