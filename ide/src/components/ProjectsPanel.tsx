import { useState } from 'react'
import { type Project } from '../lib/projects'

type ProjectsPanelProps = {
  projects: Project[]
  onSelectProject: (projectId: string, projectName: string) => void
  onClose: () => void
}

export default function ProjectsPanel({
  projects,
  onSelectProject,
  onClose,
}: ProjectsPanelProps) {
  const [searchTerm, setSearchTerm] = useState('')

  const filteredProjects = projects.filter((project) =>
    project.name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="w-full h-full flex flex-col bg-[#141414] border-l border-[#262626]">
      {/* Panel Top Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-[#171717] border-b border-[#262626] shrink-0">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-primary text-[20px]">folder</span>
          <span className="font-semibold text-white text-[14px]">
            All Projects
          </span>
          <span className="text-[10px] bg-[#262626] text-on-surface-variant px-1.5 py-0.5 rounded-full font-mono font-semibold ml-1">
            {projects.length}
          </span>
        </div>

        <button
          onClick={onClose}
          className="p-1.5 text-on-surface-variant hover:text-white rounded hover:bg-[#262626] transition-colors flex items-center justify-center cursor-pointer"
          title="Close Panel"
          type="button"
        >
          <span className="material-symbols-outlined text-[18px]">close</span>
        </button>
      </div>

      {/* Main Panel Content */}
      <div className="flex-1 flex flex-col overflow-hidden min-h-0 bg-[#0f0f10] p-6 gap-4">
        {/* Search Bar */}
        <div className="relative w-full">
          <span className="absolute left-3 top-2.5 material-symbols-outlined text-[18px] text-on-surface-variant opacity-75">
            search
          </span>
          <input
            type="text"
            placeholder="Search projects..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-[#171717] border border-[#262626] rounded-lg pl-9 pr-4 py-2 text-[12px] text-white placeholder-on-surface-variant focus:outline-none focus:border-primary transition-colors"
          />
        </div>

        {/* Projects list */}
        <div className="flex-1 overflow-y-auto pr-1 flex flex-col gap-2 scrollbar-thin">
          {filteredProjects.length === 0 ? (
            <div className="text-center py-8 text-on-surface-variant text-[12px] italic">
              {searchTerm ? 'No projects match your search.' : 'No projects available.'}
            </div>
          ) : (
            filteredProjects.map((project) => (
              <button
                key={project.id}
                onClick={() => onSelectProject(project.id, project.name)}
                className="flex items-center gap-3 w-full bg-[#171717]/80 hover:bg-[#202022] border border-[#262626]/80 hover:border-[#333333] p-3.5 rounded-xl text-left transition-all duration-150 group cursor-pointer"
                type="button"
              >
                <div className="w-10 h-10 rounded-lg bg-primary-container/10 flex items-center justify-center text-primary group-hover:scale-105 transition-transform duration-150 shrink-0">
                  <span className="material-symbols-outlined text-[20px]">
                    folder
                  </span>
                </div>
                <div className="min-w-0 flex-1">
                  <h4 className="text-[13px] font-semibold text-white truncate">
                    {project.name}
                  </h4>
                  <span className="text-[10px] text-on-surface-variant">
                    ID: {project.id.slice(0, 8)}...
                  </span>
                </div>
                <span className="material-symbols-outlined text-[16px] text-on-surface-variant opacity-0 group-hover:opacity-100 transition-opacity translate-x-1 group-hover:translate-x-0 duration-150 shrink-0">
                  arrow_forward
                </span>
              </button>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
