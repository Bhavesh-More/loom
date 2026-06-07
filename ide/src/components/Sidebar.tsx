import { useEffect, useState, useRef } from 'react'
import { getProjects, getChats, type Project, type Chat } from '../lib/projects'
import { getDownloadedAgents, type AgentData } from '../lib/agents'

export type AppPage = 'chat' | 'marketplace'

type SidebarProps = {
  activePage: AppPage
  onNavigate: (page: AppPage) => void
  activeChatId?: string | null
  onSelectChat?: (chatId: string) => void
}

function Sidebar({ activePage, onNavigate, activeChatId, onSelectChat }: SidebarProps) {
  const [projects, setProjects] = useState<Project[]>([])
  const [chats, setChats] = useState<Chat[]>([])
  const [downloadedAgents, setDownloadedAgents] = useState<AgentData[]>([])
  const [isAddingProject, setIsAddingProject] = useState(false)
  const [newProjectPath, setNewProjectPath] = useState('')
  const [newProjectName, setNewProjectName] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    let active = true

    async function loadData(force = false) {
      try {
        const [projectData, chatData, downloadedAgentData] = await Promise.all([
          getProjects(force),
          getChats(force),
          getDownloadedAgents(force),
        ])
        if (active) {
          setProjects(projectData)
          setChats(chatData)
          setDownloadedAgents(downloadedAgentData)
        }
      } catch (error) {
        console.error('Failed to fetch sidebar data', error)
      }
    }

    void loadData()

    const handleProjectCreated = () => void loadData(true)
    const handleChatCreated = () => void loadData(true)
    const handleAgentsChanged = () => void loadData(true)

    window.addEventListener('project-created', handleProjectCreated)
    window.addEventListener('chat-created', handleChatCreated)
    window.addEventListener('agents-changed', handleAgentsChanged)

    return () => {
      active = false
      window.removeEventListener('project-created', handleProjectCreated)
      window.removeEventListener('chat-created', handleChatCreated)
      window.removeEventListener('agents-changed', handleAgentsChanged)
    }
  }, [])

  const handleAddProjectClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click()
    }
  }

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (files && files.length > 0) {
      const folder = files[0] as File & { path?: string }
      const folderName = folder.name || 'New Project'
      setNewProjectName(folderName)
      setNewProjectPath(folder.path || '')
      setIsAddingProject(true)
    }
  }

  const handleSaveProject = () => {
    if (newProjectName) {
      fetch(`${import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'}/projects/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: newProjectName,
          path: newProjectPath,
        }),
      })
        .then(async (res) => {
          if (!res.ok) {
            const errorText = await res.text()
            throw new Error(errorText || 'Failed to create project')
          }
          window.dispatchEvent(new CustomEvent('project-created'))
          setIsAddingProject(false)
          setNewProjectName('')
          setNewProjectPath('')
        })
        .catch((error) => {
          console.error('Failed to create project:', error)
          alert(`Failed to create project: ${error.message}`)
        })
    }
  }

  const handleCancelAddProject = () => {
    setIsAddingProject(false)
    setNewProjectName('')
    setNewProjectPath('')
  }

  return (
    <aside
      className="hidden md:flex flex-col h-full bg-[#161616] h-screen w-sidebar-width shrink-0"
      aria-label="Workspace navigation"
    >
      {/* Brand Header */}
      <div className="px-6 py-6 flex items-center justify-between">
        <div className="flex gap-3 items-center">
          <div className="flex flex-col">
            <span className="font-headline-lg text-headline-lg font-bold text-primary dark:text-primary text-[20px] leading-none tracking-tight">
              L00m AI
            </span>
            <span className="font-label-caps text-label-caps text-on-surface-variant opacity-60 text-[10px] mt-0.5">
              Developer Workspace
            </span>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-2 flex flex-col gap-1 hide-scrollbar">
        {activePage === 'marketplace' ? (
          <button
            className="flex items-center gap-3 text-on-surface-variant dark:text-on-surface-variant hover:text-primary dark:hover:text-primary px-4 py-2 transition-all font-body-sm text-body-sm hover:bg-surface-container-highest dark:hover:bg-surface-container-high w-full text-left"
            onClick={() => onNavigate('chat')}
            type="button"
          >
            <span className="material-symbols-outlined text-[18px]">arrow_back</span>
            <span>Back to Dashboard</span>
          </button>
        ) : (
          <>
            {/* New Chat */}
            <button
              aria-current={(activePage === 'chat' && !activeChatId) ? 'page' : undefined}
              className={`flex items-center gap-3 px-4 py-2 font-body-sm text-body-sm transition-all text-left w-full ${
                (activePage === 'chat' && !activeChatId)
                  ? 'text-primary dark:text-primary border-l-2 border-primary bg-surface-container-high dark:bg-surface-container-highest'
                  : 'text-on-surface-variant dark:text-on-surface-variant hover:text-primary dark:hover:text-primary hover:bg-surface-container-highest dark:hover:bg-surface-container-high'
              }`}
              onClick={() => onNavigate('chat')}
              type="button"
            >
              <span className="material-symbols-outlined text-[18px]">add_box</span>
              <span>New chat</span>
            </button>

            {/* Marketplace */}
            <button
              aria-current={(activePage as string) === 'marketplace' ? 'page' : undefined}
              className={`flex items-center gap-3 px-4 py-2 font-body-sm text-body-sm transition-all text-left w-full ${
                (activePage as string) === 'marketplace'
                  ? 'text-primary dark:text-primary border-l-2 border-primary bg-surface-container-high dark:bg-surface-container-highest'
                  : 'text-on-surface-variant dark:text-on-surface-variant hover:text-primary dark:hover:text-primary hover:bg-surface-container-highest dark:hover:bg-surface-container-high'
              }`}
              onClick={() => onNavigate('marketplace')}
              type="button"
            >
              <span className="material-symbols-outlined text-[18px]">storefront</span>
              <span>Marketplace</span>
            </button>

            {/* Other links */}
            {/* <a
              className="flex items-center gap-3 text-on-surface-variant dark:text-on-surface-variant hover:text-primary dark:hover:text-primary px-4 py-2 transition-colors font-body-sm text-body-sm hover:bg-surface-container-highest dark:hover:bg-surface-container-high"
              href="#"
            >
              <span className="material-symbols-outlined text-[18px]">extension</span>
              <span>Plugins</span>
            </a>
            <a
              className="flex items-center gap-3 text-on-surface-variant dark:text-on-surface-variant hover:text-primary dark:hover:text-primary px-4 py-2 transition-colors font-body-sm text-body-sm hover:bg-surface-container-highest dark:hover:bg-surface-container-high"
              href="#"
            >
              <span className="material-symbols-outlined text-[18px]">smart_toy</span>
              <span>Automations</span>
            </a> */}

            {/* ── Projects ───────────────────────────────────────── */}
            <div
              className="mt-2 p-2 px-4 mb-1 flex items-center justify-between cursor-pointer hover:bg-surface-container-high dark:hover:bg-surface-container-high rounded px-2"
              onClick={handleAddProjectClick}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && handleAddProjectClick()}
              title="Add existing project"
            >
              <span className="text-label-caps text-on-surface-variant opacity-70 text-[11px] tracking-widest">
                Projects
              </span>
              <span className="material-symbols-outlined text-[16px] text-on-surface-variant opacity-70 hover:text-primary dark:hover:text-primary transition-colors">
                add
              </span>
              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                onChange={handleFileSelect}
              />
            </div>

            {projects.length > 0 ? (
              projects.map((project) => (
                <a
                  className="flex items-center gap-3 text-on-surface-variant dark:text-on-surface-variant hover:text-primary dark:hover:text-primary px-4 py-2 transition-all font-body-sm text-body-sm hover:bg-surface-container-highest dark:hover:bg-surface-container-high cursor-pointer"
                  href="#"
                  key={project.id}
                >
                  <span className="material-symbols-outlined text-[18px] opacity-70">folder</span>
                  <span className="truncate">{project.name}</span>
                </a>
              ))
            ) : null}

            {/* Add Project Modal/Dialog */}
            {isAddingProject && (
              <div className="px-4 py-3 bg-surface-container-high dark:bg-surface-container-high rounded-lg mb-2 animate-step-fade-in">
                <div className="flex items-center gap-3 mb-3">
                  <span className="material-symbols-outlined text-primary text-[20px]">folder_open</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-primary font-medium text-[13px] truncate">{newProjectName}</p>
                    <p className="text-on-surface-variant text-[11px] truncate">{newProjectPath}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleCancelAddProject}
                    className="flex items-center gap-1.5 text-on-surface-variant hover:text-primary text-[11px] px-2 py-1 hover:bg-surface-container-high rounded transition-colors"
                    type="button"
                  >
                    <span className="material-symbols-outlined text-[16px]">close</span>
                    Cancel
                  </button>
                  <div className="flex-1" />
                  <button
                    onClick={handleSaveProject}
                    className="flex items-center gap-1.5 text-on-primary bg-primary hover:bg-primary/90 text-[11px] px-3 py-1.5 rounded transition-colors"
                    type="button"
                  >
                    <span className="material-symbols-outlined text-[16px]">save</span>
                    Save
                  </button>
                </div>
              </div>
            )}

            <div className="mt-5 px-4 mb-2">
              <span className="font-label-caps text-label-caps text-on-surface-variant opacity-70 text-[11px] tracking-widest ">
                Agents
              </span>
            </div>

            {downloadedAgents.length > 0 ? (
              <div className="px-3 flex flex-col gap-2">
                {downloadedAgents.slice(0, 4).map((agent) => (
                  <div
                    key={agent.id}
                    className="rounded-xl border border-outline-variant/30 bg-surface-container-low px-3 py-3"
                  >
                    <div className="flex items-start gap-3">
                      <div className={`market-icon market-icon--${agent.tone} !w-10 !h-10 !rounded-lg shrink-0`}>
                        <span className="material-symbols-outlined text-[18px]">{agent.icon}</span>
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center justify-between gap-2">
                          <span className="text-[12px] font-medium text-on-surface truncate">
                            {agent.name}
                          </span>
                          <span className="text-[10px] text-primary shrink-0">Downloaded</span>
                        </div>
                        <div className="mt-1 text-[10px] text-on-surface-variant">
                          {agent.category} · {agent.type}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                {downloadedAgents.length > 4 ? (
                  <button
                    className="text-left px-2 py-1 text-[11px] text-on-surface-variant hover:text-primary transition-colors"
                    onClick={() => onNavigate('marketplace')}
                    type="button"
                  >
                    View all {downloadedAgents.length} agents
                  </button>
                ) : null}
              </div>
            ) : (
              <span className="px-4 py-1.5 text-[12px] text-on-surface-variant italic">
                No agents downloaded yet
              </span>
            )}


            {/* ── Chats ─────────────────────────────────────────── */}
            <div className="mt-5 px-4 mb-1">
              <span className="font-label-caps text-label-caps text-on-surface-variant opacity-70 text-[11px] tracking-widest ">
                Chats
              </span>
            </div>

            {chats.length > 0 ? (
              chats.map((chat) => {
                const isActive = activeChatId === chat.id
                return (
                  <button
                    className={`flex items-center gap-3 px-4 py-2 font-body-sm text-body-sm transition-all text-left w-full ${
                      isActive
                        ? 'text-primary dark:text-primary border-l-2 border-primary bg-surface-container-high dark:bg-surface-container-highest font-medium'
                        : 'text-on-surface-variant dark:text-on-surface-variant hover:text-primary dark:hover:text-primary hover:bg-surface-container-highest dark:hover:bg-surface-container-high'
                    }`}
                    onClick={() => {
                      onNavigate('chat')
                      if (onSelectChat) {
                        onSelectChat(chat.id)
                      }
                    }}
                    type="button"
                    key={chat.id}
                    title={chat.title}
                  >
                    <span className="material-symbols-outlined text-[18px] opacity-70">chat</span>
                    <span className="truncate">{chat.title}</span>
                  </button>
                )
              })
            ) : (
              <span className="px-4 py-1.5 text-[12px] text-on-surface-variant italic">
                No chats yet
              </span>
            )}
          </>
        )}
      </nav>

      {/* Footer */}
      <div className="marketplace-sidebar-footer mt-auto border-t border-outline-variant py-2">

        <a
          className="flex items-center gap-3 text-on-surface-variant dark:text-on-surface-variant hover:text-primary dark:hover:text-primary px-4 py-2 transition-all font-body-sm text-body-sm hover:bg-surface-container-highest dark:hover:bg-surface-container-high"
          href="#"
        >
          <span className="material-symbols-outlined text-[18px]">settings</span>
          <span>Settings</span>
        </a>
      </div>
    </aside>
  )
}

export default Sidebar
