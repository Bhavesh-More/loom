import { type ChangeEvent, useEffect, useRef, useState } from 'react'
import { getProjects, developProject, type Project } from '../lib/projects'
import { getDownloadedAgents, type AgentData } from '../lib/agents'

type PromptComposerProps = {
  onSendPrompt?: (projectId: string, prompt: string, selectedAgentIds: string[]) => Promise<void> | void
  isDevelopingProps?: boolean
}

function PromptComposer({ onSendPrompt, isDevelopingProps }: PromptComposerProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const agentDropdownRef = useRef<HTMLDivElement>(null)
  const [prompt, setPrompt] = useState('')
  const [selectedProjectId, setSelectedProjectId] = useState('')
  const [newProjectName, setNewProjectName] = useState('')
  const [isDevelopingState, setIsDevelopingState] = useState(false)
  const isDeveloping = isDevelopingProps !== undefined ? isDevelopingProps : isDevelopingState
  const [developError, setDevelopError] = useState('')
  const [developSuccess, setDevelopSuccess] = useState('')
  
  // Custom states for permission, model, agents, and ripple effect
  const [permission, setPermission] = useState('default')
  const [selectedModel, setSelectedModel] = useState('gemini-1.5-pro')
  const [projects, setProjects] = useState<Project[]>([])
  const [downloadedAgents, setDownloadedAgents] = useState<AgentData[]>([])
  const [selectedAgents, setSelectedAgents] = useState<string[]>([])
  const [isAgentDropdownOpen, setIsAgentDropdownOpen] = useState(false)
  const [isRippling, setIsRippling] = useState(false)

  const handleChange = (event: ChangeEvent<HTMLTextAreaElement>) => {
    setPrompt(event.target.value)

    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = `${textarea.scrollHeight}px`
    }
  }

  const handleSend = async () => {
    if (!prompt.trim() || !selectedProjectId || selectedAgents.length === 0 || isDeveloping) {
      return
    }

    if (selectedProjectId === 'new-project' && !newProjectName.trim()) {
      setDevelopError('Please enter a project name for the new project.')
      return
    }

    // Trigger Siri-like ripple effect for 2.5 seconds
    setIsRippling(true)
    setTimeout(() => {
      setIsRippling(false)
    }, 2500)

    let projectIdToDevelop = selectedProjectId

    if (selectedProjectId === 'new-project') {
      setIsDevelopingState(true)
      setDevelopError('')
      setDevelopSuccess('')
      try {
        const response = await fetch(`${import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'}/projects`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            name: newProjectName.trim(),
            description: `Created for: ${prompt.trim().substring(0, 100)}`,
            agent_ids: selectedAgents,
          }),
        })
        if (!response.ok) {
          const errText = await response.text()
          throw new Error(errText || 'Failed to create new project')
        }
        const newProj = await response.json()
        projectIdToDevelop = newProj.project_id
        // Dispatch event to notify Sidebar and other components
        window.dispatchEvent(new CustomEvent('project-created'))
        setNewProjectName('')
      } catch (err: any) {
        setDevelopError(err.message || 'Failed to create new project')
        setIsDevelopingState(false)
        return
      }
    }

    if (onSendPrompt) {
      void onSendPrompt(projectIdToDevelop, prompt.trim(), selectedAgents)
      setPrompt('')
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'
      }
      return
    }

    setIsDevelopingState(true)
    setDevelopError('')
    setDevelopSuccess('')

    try {
      const result = await developProject(projectIdToDevelop, prompt.trim(), selectedAgents)
      let successMsg = `Successfully developed project! Files written to: ${result.workspace_path}`
      if (result.errors && result.errors.length > 0) {
        successMsg += ` (with errors: ${result.errors.join(', ')})`
      }
      setDevelopSuccess(successMsg)
      setPrompt('')
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'
      }
    } catch (error) {
      setDevelopError(error instanceof Error ? error.message : 'Failed to develop project')
    } finally {
      setIsDevelopingState(false)
    }
  }

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      void handleSend()
    }
  }

  useEffect(() => {
    let active = true

    async function loadComposerData(force = false) {
      try {
        const [projectData, downloadedAgentData] = await Promise.all([
          getProjects(force),
          getDownloadedAgents(force),
        ])
        if (!active) {
          return
        }

        setProjects(projectData)
        setDownloadedAgents(downloadedAgentData)
        setSelectedProjectId((currentProjectId) => {
          if (currentProjectId === 'new-project') {
            return 'new-project'
          }
          if (projectData.some((project) => project.id === currentProjectId)) {
            return currentProjectId
          }

          return 'new-project'
        })
        setSelectedAgents((currentSelectedAgents) => {
          const availableAgentIds = new Set(downloadedAgentData.map((agent) => agent.id))
          const filteredAgentIds = currentSelectedAgents.filter((agentId) =>
            availableAgentIds.has(agentId),
          )

          if (filteredAgentIds.length > 0) {
            return filteredAgentIds
          }

          return downloadedAgentData.slice(0, 2).map((agent) => agent.id)
        })
      } catch (error) {
        console.error('Failed to load composer data', error)
      }
    }

    void loadComposerData()

    const handleProjectCreated = () => {
      void loadComposerData(true)
    }
    const handleAgentsChanged = () => {
      void loadComposerData(true)
    }

    window.addEventListener('project-created', handleProjectCreated)
    window.addEventListener('agents-changed', handleAgentsChanged)

    return () => {
      active = false
      window.removeEventListener('project-created', handleProjectCreated)
      window.removeEventListener('agents-changed', handleAgentsChanged)
    }
  }, [])

  // Close agent dropdown on click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (agentDropdownRef.current && !agentDropdownRef.current.contains(event.target as Node)) {
        setIsAgentDropdownOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [])

  return (
    <section className="w-full relative" aria-label="Project prompt composer">
      {/* Siri style tag for keyframe animations */}
      <style>{`
        @keyframes siri-ripple {
          0% {
            box-shadow: 0 0 0 0 rgba(147, 51, 234, 0.6), 0 0 0 0 rgba(59, 130, 246, 0.4);
          }
          50% {
            box-shadow: 0 0 0 10px rgba(147, 51, 234, 0.3), 0 0 0 20px rgba(59, 130, 246, 0.1);
          }
          100% {
            box-shadow: 0 0 0 20px rgba(147, 51, 234, 0), 0 0 0 30px rgba(59, 130, 246, 0);
          }
        }
        @keyframes border-glow {
          0%, 100% {
            border-color: rgba(147, 51, 234, 0.8);
          }
          50% {
            border-color: rgba(59, 130, 246, 0.8);
          }
        }
        .siri-active {
          animation: border-glow 1.2s infinite ease-in-out !important;
        }
        .siri-ripple-container {
          position: absolute;
          inset: -2px;
          border-radius: 26px;
          pointer-events: none;
          z-index: 0;
          animation: siri-ripple 1.2s infinite cubic-bezier(0.1, 0.8, 0.3, 1);
        }
        /* Hide native arrow and style select elements completely */
        select {
          -webkit-appearance: none !important;
          -moz-appearance: none !important;
          appearance: none !important;
          background-color: transparent !important;
          color: inherit !important;
          border: none !important;
        }
        select::-ms-expand {
          display: none !important;
        }
        /* Style select options for dark theme */
        select option {
          background-color: #171717 !important;
          color: #e5e2e1 !important;
        }
      `}</style>

      <div className="relative group">
        {isRippling && <div className="siri-ripple-container" />}
        
        <div className={`bg-surface-container-low border border-outline-variant rounded-[24px] flex flex-col shadow-2xl relative z-10 transition-colors duration-300 ${isRippling ? 'siri-active' : ''}`}>
          {/* Project Name Input */}
          {selectedProjectId === 'new-project' && (
            <div className="px-6 pt-5 pb-2 border-b border-outline-variant/30 flex items-center gap-2">
              <span className="material-symbols-outlined text-[18px] text-on-surface-variant">create_new_folder</span>
              <input
                type="text"
                className="w-full bg-transparent border-none outline-none focus:ring-0 text-primary placeholder:text-outline/40 text-[14px] font-medium p-0"
                placeholder="Enter new project name (e.g., Task Manager)"
                value={newProjectName}
                onChange={(e) => setNewProjectName(e.target.value)}
                disabled={isDeveloping}
              />
            </div>
          )}
          {/* Text Area */}
          <div className="p-6">
            <textarea
              aria-label="Prompt"
              className="w-full bg-transparent border-none outline-none focus:ring-0 focus:border-transparent focus:outline-none font-body-lg text-body-lg text-on-surface resize-none placeholder:text-outline/60 p-0 m-0"
              onChange={handleChange}
              onKeyDown={handleKeyDown}
              placeholder="How can i help you today?"
              ref={textareaRef}
              rows={2}
              value={prompt}
              disabled={isDeveloping}
            />
          </div>

          {/* Action Bar */}
          <div className="flex flex-wrap items-center justify-between px-4 py-3 border-t border-outline-variant/50 bg-surface-container-lowest/50 gap-3">
            <div className="flex flex-wrap items-center gap-2">
              <button className="p-2 text-on-surface-variant hover:text-white rounded-full hover:bg-surface-variant/30 transition-colors" type="button" aria-label="Add attachment" disabled={isDeveloping}>
                <span className="material-symbols-outlined text-[20px]">add</span>
              </button>

              {/* Permission Selector */}
              <div className="flex items-center gap-1.5 px-3 py-1 text-on-surface-variant hover:text-white rounded-full border border-outline-variant/30 hover:bg-surface-variant/30 transition-colors relative cursor-pointer max-w-[220px]">
                <span className="material-symbols-outlined text-[16px] pointer-events-none">folder</span>
                <select
                  aria-label="Select project"
                  className="bg-transparent border-none outline-none focus:ring-0 focus:border-transparent focus:outline-none text-inherit font-inherit font-label-caps text-[11px] py-0 pl-0 pr-5 cursor-pointer select-none appearance-none min-w-0 truncate"
                  value={selectedProjectId}
                  onChange={(event) => setSelectedProjectId(event.target.value)}
                  disabled={isDeveloping}
                >
                  <option value="new-project" className="bg-surface text-on-surface font-semibold text-secondary">
                    + Create New Project
                  </option>
                  {projects.map((project) => (
                    <option key={project.id} value={project.id} className="bg-surface text-on-surface">
                      {project.name}
                    </option>
                  ))}
                </select>
                <span className="material-symbols-outlined text-[16px] absolute right-2 pointer-events-none">keyboard_arrow_down</span>
              </div>

              {/* Permission Selector */}
              <div className="flex items-center gap-1.5 px-3 py-1 text-on-surface-variant hover:text-white rounded-full border border-outline-variant/30 hover:bg-surface-variant/30 transition-colors relative cursor-pointer">
                <span className="material-symbols-outlined text-[16px] pointer-events-none">back_hand</span>
                <select
                  aria-label="Permission level"
                  className="bg-transparent border-none outline-none focus:ring-0 focus:border-transparent focus:outline-none text-inherit font-inherit font-label-caps text-[11px] py-0 pl-0 pr-4 cursor-pointer select-none appearance-none"
                  value={permission}
                  onChange={(e) => setPermission(e.target.value)}
                  disabled={isDeveloping}
                  style={{ paddingRight: '12px' }}
                >
                  <option value="default" className="bg-surface text-on-surface">Default permissions</option>
                  <option value="auto-review" className="bg-surface text-on-surface">Auto-review</option>
                  <option value="full-access" className="bg-surface text-on-surface">Full Access</option>
                </select>
                <span className="material-symbols-outlined text-[16px] absolute right-2 pointer-events-none">keyboard_arrow_down</span>
              </div>

              {/* Model Selector */}
              <div className="flex items-center gap-1.5 px-3 py-1 text-on-surface-variant hover:text-white rounded-full border border-outline-variant/30 hover:bg-surface-variant/30 transition-colors relative cursor-pointer">
                <select
                  aria-label="Select model"
                  className="bg-transparent border-none outline-none focus:ring-0 focus:border-transparent focus:outline-none text-inherit font-inherit font-label-caps text-[11px] py-0 pl-0 pr-4 cursor-pointer select-none appearance-none"
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  disabled={isDeveloping}
                  style={{ paddingRight: '12px' }}
                >
                  <option value="gemini-1.5-pro" className="bg-surface text-on-surface">Gemini 1.5 Pro</option>
                  <option value="gemini-1.5-flash" className="bg-surface text-on-surface">Gemini 1.5 Flash</option>
                  <option value="gemini-2.0-flash" className="bg-surface text-on-surface">Gemini 2.0 Flash</option>
                </select>
              </div>

              {/* Agent Selector (Multi-select) */}
              <div ref={agentDropdownRef} className="relative">
                <button
                  className="flex items-center gap-2 px-3 py-1 text-on-surface-variant hover:text-white rounded-full border border-outline-variant/30 hover:bg-surface-variant/30 transition-colors cursor-pointer text-left"
                  type="button"
                  onClick={() => setIsAgentDropdownOpen(!isAgentDropdownOpen)}
                  disabled={isDeveloping}
                >
                  <div className="flex -space-x-1.5 pointer-events-none" aria-hidden="true">
                    {selectedAgents.map((agentId) => {
                      const agent = downloadedAgents.find((a) => a.id === agentId)
                      if (!agent) return null
                      return (
                        <div key={agent.id} className="w-5 h-5 rounded-md bg-surface-container-highest flex items-center justify-center border border-background">
                          <span className="material-symbols-outlined text-[12px]">{agent.icon}</span> 
                        </div>
                      )
                    })}
                  </div>
                  <span className="font-label-caps text-[11px]">
                    {selectedAgents.length === 0
                      ? 'No Agents'
                      : selectedAgents.length === 1
                      ? downloadedAgents.find((a) => a.id === selectedAgents[0])?.name
                      : 'Agents'}
                  </span>
                  {selectedAgents.length > 2 && (
                    <span className="font-label-caps text-[10px] bg-secondary-container/20 text-secondary px-1.5 rounded-full">
                      +{selectedAgents.length - 2}
                    </span>
                  )}
                  <span className="material-symbols-outlined text-[16px]">keyboard_arrow_down</span>
                </button>

                {isAgentDropdownOpen && (
                  <div className="absolute left-0 bottom-full mb-2 z-50 min-w-[200px] bg-surface-container-low border border-outline-variant rounded-[12px] p-2 shadow-xl flex flex-col gap-1">
                    {downloadedAgents.length === 0 ? (
                      <div className="px-3 py-2 text-[12px] text-on-surface-variant">
                        Download agents from Marketplace first.
                      </div>
                    ) : downloadedAgents.map((agent) => {
                      const isSelected = selectedAgents.includes(agent.id)
                      return (
                        <div
                          key={agent.id}
                          className="flex items-center gap-2 px-3 py-2 hover:bg-surface-variant/30 rounded-md cursor-pointer text-on-surface select-none text-[12px]"
                          onClick={() => {
                            if (isSelected) {
                              setSelectedAgents(selectedAgents.filter((id) => id !== agent.id))
                            } else {
                              setSelectedAgents([...selectedAgents, agent.id])
                            }
                          }}
                        >
                          <span className="material-symbols-outlined text-[18px] text-primary">
                            {isSelected ? 'check_box' : 'check_box_outline_blank'}
                          </span>
                          <span className="material-symbols-outlined text-[16px]">{agent.icon}</span>
                          <span className="font-body-sm">{agent.name}</span>
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            </div>

            <div className="flex items-center gap-2 ml-auto">
              <button className="p-2 text-on-surface-variant hover:text-white rounded-full hover:bg-surface-variant/30 transition-colors" type="button" aria-label="Use microphone" disabled={isDeveloping}>
                <span className="material-symbols-outlined text-[20px]">mic</span>
              </button>
              <button
                className={`w-8 h-8 rounded-full flex items-center justify-center transition-all ${
                  !prompt.trim() || !selectedProjectId || selectedAgents.length === 0 || isDeveloping
                    ? 'bg-on-surface-variant/20 text-on-surface-variant/40 cursor-not-allowed'
                    : 'bg-primary text-on-primary hover:bg-opacity-90 active:scale-95'
                }`}
                disabled={!prompt.trim() || !selectedProjectId || selectedAgents.length === 0 || isDeveloping}
                type="button"
                aria-label="Send prompt"
                onClick={handleSend}
              >
                <span className="material-symbols-outlined text-[20px]">
                  {isDeveloping ? 'progress_activity' : 'arrow_upward'}
                </span>
              </button>
            </div>
          </div>

          {/* Metadata Context Bar
          <div className="flex flex-wrap items-center gap-4 px-6 py-2 bg-surface-container-lowest border-t border-outline-variant/30 rounded-b-[24px]">
            Project selector styled exactly as context chip
            <div className="flex items-center gap-1.5 text-[11px] font-label-caps text-outline hover:text-on-surface cursor-pointer transition-colors relative">
              <span className="material-symbols-outlined text-[14px]">folder</span>
              <select
                aria-label="Select project"
                className="bg-transparent border-none outline-none focus:ring-0 focus:border-transparent focus:outline-none text-inherit font-inherit py-0 pl-0 pr-4 cursor-pointer select-none appearance-none"
                onChange={(event) => setSelectedProjectId(event.target.value)}
                value={selectedProjectId}
                disabled={isDeveloping}
                style={{ paddingRight: '12px' }}
              >
                {projects.length > 0 ? (
                  projects.map((project) => (
                    <option key={project.id} value={project.id} className="bg-surface text-on-surface">
                      {project.name}
                    </option>
                  ))
                ) : (
                  <option value="" className="bg-surface text-on-surface">No projects</option>
                )}
              </select>
              <span className="material-symbols-outlined text-[16px] absolute right-0 pointer-events-none">keyboard_arrow_down</span>
            </div>

            {contextItems.map((item) => (
              <div 
                className="flex items-center gap-1 text-[11px] font-label-caps text-outline hover:text-on-surface cursor-pointer transition-colors relative bg-transparent" 
                key={item.label}
              >
                <span className="material-symbols-outlined text-[14px] pointer-events-none">{item.icon}</span>
                <select
                  aria-label={`Select ${item.label}`}
                  className="bg-transparent border-none outline-none focus:ring-0 focus:border-transparent focus:outline-none text-inherit font-inherit py-0 pl-0 pr-4 cursor-pointer select-none appearance-none"
                  disabled={isDeveloping}
                  style={{ paddingRight: '12px' }}
                  defaultValue={item.label}
                >
                  <option value={item.label} className="bg-surface text-on-surface">{item.label}</option>
                  {item.label === 'Work locally' ? (
                    <>
                      <option value="Work in cloud" className="bg-surface text-on-surface">Work in cloud</option>
                      <option value="Work on staging" className="bg-surface text-on-surface">Work on staging</option>
                    </>
                  ) : item.label === 'main' ? (
                    <>
                      <option value="dev" className="bg-surface text-on-surface">dev</option>
                      <option value="staging" className="bg-surface text-on-surface">staging</option>
                    </>
                  ) : null}
                </select>
                <span className="material-symbols-outlined text-[16px] absolute right-0 pointer-events-none">keyboard_arrow_down</span>
              </div>
            ))}
          </div> */}
        </div>
      </div>

      {developError ? (
        <div className="text-error font-body-sm text-[13px] mt-3 px-2 flex items-center gap-2">
          <span className="material-symbols-outlined text-[16px]">error</span>
          <span>{developError}</span>
        </div>
      ) : null}
      {developSuccess ? (
        <div className="text-tertiary-fixed-dim font-body-sm text-[13px] mt-3 px-2 flex items-center gap-2">
          <span className="material-symbols-outlined text-[16px]">check_circle</span>
          <span>{developSuccess}</span>
        </div>
      ) : null}
    </section>
  )
}

export default PromptComposer
