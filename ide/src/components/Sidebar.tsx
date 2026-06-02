import { useEffect, useState } from 'react'
import { getProjects, getChats, type Project, type Chat } from '../lib/projects'

export type AppPage = 'chat' | 'marketplace'

type SidebarProps = {
  activePage: AppPage
  onNavigate: (page: AppPage) => void
}

function Sidebar({ activePage, onNavigate }: SidebarProps) {
  const [projects, setProjects] = useState<Project[]>([])
  const [chats, setChats] = useState<Chat[]>([])

  useEffect(() => {
    let active = true

    async function loadData(force = false) {
      try {
        const [projectData, chatData] = await Promise.all([
          getProjects(force),
          getChats(force),
        ])
        if (active) {
          setProjects(projectData)
          setChats(chatData)
        }
      } catch (error) {
        console.error('Failed to fetch sidebar data', error)
      }
    }

    void loadData()

    const handleProjectCreated = () => void loadData(true)
    const handleChatCreated = () => void loadData(true)

    window.addEventListener('project-created', handleProjectCreated)
    window.addEventListener('chat-created', handleChatCreated)

    return () => {
      active = false
      window.removeEventListener('project-created', handleProjectCreated)
      window.removeEventListener('chat-created', handleChatCreated)
    }
  }, [])

  return (
    <aside
      className="hidden md:flex flex-col h-full border-r border-outline-variant bg-surface-container-low dark:bg-surface-container-lowest h-screen w-sidebar-width shrink-0"
      aria-label="Workspace navigation"
    >
      {/* Brand Header */}
      <div className="px-6 py-6 flex items-center justify-between">
        <div className="flex gap-3 items-center">
          <span className="material-symbols-outlined text-primary text-[24px]">robot_2</span>
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
              aria-current={activePage === 'chat' ? 'page' : undefined}
              className={`flex items-center gap-3 px-4 py-2 font-body-sm text-body-sm transition-all text-left w-full ${
                activePage === 'chat'
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
            <a
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
            </a>

            {/* ── Projects ───────────────────────────────────────── */}
            <div className="mt-6 px-4 mb-1">
              <span className="font-label-caps text-label-caps text-on-surface-variant opacity-70 text-[11px] tracking-widest uppercase">
                Projects
              </span>
            </div>

            {projects.length > 0 ? (
              projects.map((project) => (
                <a
                  className="flex items-center gap-3 text-on-surface-variant dark:text-on-surface-variant hover:text-primary dark:hover:text-primary px-4 py-2 transition-all font-body-sm text-body-sm hover:bg-surface-container-highest dark:hover:bg-surface-container-high"
                  href="#"
                  key={project.id}
                >
                  <span className="material-symbols-outlined text-[18px] opacity-70">folder</span>
                  <span className="truncate">{project.name}</span>
                </a>
              ))
            ) : (
              <span className="px-4 py-1.5 text-[12px] text-on-surface-variant italic">
                No projects yet
              </span>
            )}

            {/* ── Chats ─────────────────────────────────────────── */}
            <div className="mt-5 px-4 mb-1">
              <span className="font-label-caps text-label-caps text-on-surface-variant opacity-70 text-[11px] tracking-widest uppercase">
                Chats
              </span>
            </div>

            {chats.length > 0 ? (
              chats.map((chat) => (
                <a
                  className="flex items-center gap-3 text-on-surface-variant dark:text-on-surface-variant hover:text-primary dark:hover:text-primary px-4 py-2 transition-all font-body-sm text-body-sm hover:bg-surface-container-highest dark:hover:bg-surface-container-high"
                  href="#"
                  key={chat.id}
                  title={chat.title}
                >
                  <span className="material-symbols-outlined text-[18px] opacity-70">chat</span>
                  <span className="truncate">{chat.title}</span>
                </a>
              ))
            ) : (
              <span className="px-4 py-1.5 text-[12px] text-on-surface-variant italic">
                No chats yet
              </span>
            )}
          </>
        )}
      </nav>

      {/* Footer */}
      <div className="mt-auto border-t border-outline-variant py-2">
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
