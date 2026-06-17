
type TopAppBarProps = {
  projectName?: string
  prompt?: string
  isSessionActive?: boolean
  isWorkspaceOpen?: boolean
  onToggleWorkspace?: () => void
}

function TopAppBar({ projectName, prompt, isSessionActive, isWorkspaceOpen = true, onToggleWorkspace }: TopAppBarProps) {
  if (isSessionActive) {
    return (
      <header className="h-14 flex items-center justify-between px-6 border-b border-[#262626] bg-[#0A0A0A] shrink-0 w-full z-10">
        <div className="flex items-center gap-2 font-code-md text-code-md text-on-surface-variant text-[14px]">
          <span className="material-symbols-outlined text-[18px]">folder</span>
          <span className="font-semibold text-primary">{projectName || 'project'}</span>
          <span className="material-symbols-outlined text-[16px] mx-1 opacity-50">chevron_right</span>
          <span className="truncate max-w-[280px] md:max-w-[450px] opacity-75">{prompt || 'Agent execution'}</span>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1 bg-[#171717] border border-[#262626] rounded-full font-code-md text-[12px] text-on-surface-variant">
            <span className="material-symbols-outlined text-[14px]">commit</span>
            <span>main</span>
          </div>
          <div className="flex gap-2">
            <button className="p-1.5 text-on-surface-variant hover:text-white rounded hover:bg-[#262626] transition-colors" type="button" aria-label="Information">
              <span className="material-symbols-outlined text-[18px]">info</span>
            </button>
            <button
              className="p-1.5 text-on-surface-variant hover:text-white rounded hover:bg-[#262626] transition-colors"
              type="button"
              aria-label={isWorkspaceOpen ? 'Hide workspace explorer' : 'Show workspace explorer'}
              title={isWorkspaceOpen ? 'Hide workspace explorer' : 'Show workspace explorer'}
              onClick={onToggleWorkspace}
            >
              <span className="material-symbols-outlined text-[18px]">dock_to_right</span>
            </button>
          </div>
        </div>
      </header>
    )
  }

  return (
    <header className="flex justify-between items-center px-6 py-4 w-full bg-transparent absolute top-0 left-0 z-10">
      <div className="flex items-center gap-6">
        <nav className="hidden md:flex gap-6 items-center" aria-label="Workspace sections">
          <a className="font-label-caps text-label-caps text-on-surface-variant hover:text-primary transition-colors text-[12px]" href="#">
            Models
          </a>
        </nav>
      </div>

      <div className="flex items-center gap-4">
        <button className="p-2 text-on-surface-variant hover:bg-surface-variant/20 rounded-xl transition-all active:scale-95" type="button" aria-label="Grid View">
          <span className="material-symbols-outlined text-[20px]">grid_view</span>
        </button>
        <button className="p-2 text-on-surface-variant hover:bg-surface-variant/20 rounded-xl transition-all active:scale-95" type="button" aria-label="Sidebar Right">
          <span className="material-symbols-outlined text-[20px]">view_sidebar</span>
        </button>
      </div>
    </header>
  )
}

export default TopAppBar
