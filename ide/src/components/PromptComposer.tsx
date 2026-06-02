import { type ChangeEvent, useEffect, useRef, useState } from 'react'
import { getProjects, type Project, developProject } from '../lib/projects'

const contextItems = [
  { label: 'Work locally', icon: 'laptop_windows' },
  { label: 'main', icon: 'account_tree' },
]

type PromptComposerProps = {
  onSendPrompt?: (projectId: string, prompt: string) => Promise<void> | void
  isDevelopingProps?: boolean
}

function PromptComposer({ onSendPrompt, isDevelopingProps }: PromptComposerProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const [prompt, setPrompt] = useState('')
  const [projects, setProjects] = useState<Project[]>([])
  const [selectedProjectId, setSelectedProjectId] = useState('')
  const [isDevelopingState, setIsDevelopingState] = useState(false)
  const isDeveloping = isDevelopingProps !== undefined ? isDevelopingProps : isDevelopingState
  const [developError, setDevelopError] = useState('')
  const [developSuccess, setDevelopSuccess] = useState('')

  const handleChange = (event: ChangeEvent<HTMLTextAreaElement>) => {
    setPrompt(event.target.value)

    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = `${textarea.scrollHeight}px`
    }
  }

  const handleSend = async () => {
    if (!prompt.trim() || !selectedProjectId || isDeveloping) {
      return
    }

    if (onSendPrompt) {
      void onSendPrompt(selectedProjectId, prompt.trim())
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
      const result = await developProject(selectedProjectId, prompt.trim())
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

    async function loadProjects(force = false) {
      try {
        const data = await getProjects(force)
        if (!active) {
          return
        }

        setProjects(data)
        setSelectedProjectId((currentProjectId) => {
          if (data.some((project) => project.id === currentProjectId)) {
            return currentProjectId
          }

          return data[0]?.id ?? ''
        })
      } catch (error) {
        console.error('Failed to load composer projects', error)
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
    <section className="w-full" aria-label="Project prompt composer">
      <div className="bg-surface-container-low border border-outline-variant rounded-[24px] overflow-hidden flex flex-col shadow-2xl">
        {/* Text Area */}
        <div className="p-6">
          <textarea
            aria-label="Prompt"
            className="w-full bg-transparent border-none outline-none focus:ring-0 focus:border-transparent focus:outline-none font-body-lg text-body-lg text-on-surface resize-none placeholder:text-outline/60 p-0 m-0"
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            placeholder="Do anything"
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

            <button className="flex items-center gap-1.5 px-3 py-1 text-on-surface-variant hover:text-white rounded-full border border-outline-variant/30 hover:bg-surface-variant/30 transition-colors" type="button" disabled={isDeveloping}>
              <span className="material-symbols-outlined text-[16px]">back_hand</span>
              <span className="font-label-caps text-[11px]">Default permissions</span>
              <span className="material-symbols-outlined text-[16px]">keyboard_arrow_down</span>
            </button>

            <button className="flex items-center gap-1.5 px-3 py-1 text-on-surface-variant hover:text-white rounded-full border border-outline-variant/30 hover:bg-surface-variant/30 transition-colors" type="button" disabled={isDeveloping}>
              <span className="font-label-caps text-[11px] font-bold">5.5</span>
              <span className="font-label-caps text-[11px]">High</span>
              <span className="material-symbols-outlined text-[16px]">keyboard_arrow_down</span>
            </button>

            <button className="flex items-center gap-2 px-2 py-1 text-on-surface-variant hover:text-white rounded-full border border-outline-variant/30 hover:bg-surface-variant/30 transition-colors" type="button" disabled={isDeveloping}>
              <div className="flex -space-x-1.5" aria-hidden="true">
                <div className="w-5 h-5 rounded-md bg-surface-container-highest flex items-center justify-center border border-background">
                  <span className="material-symbols-outlined text-[12px]">smart_toy</span>
                </div>
                <div className="w-5 h-5 rounded-md bg-surface-container-highest flex items-center justify-center border border-background">
                  <span className="material-symbols-outlined text-[12px]">psychology</span>
                </div>
              </div>
              <span className="font-label-caps text-[10px] bg-secondary-container/20 text-secondary px-1.5 rounded-full">+2</span>
              <span className="material-symbols-outlined text-[16px]">keyboard_arrow_down</span>
            </button>
          </div>

          <div className="flex items-center gap-2 ml-auto">
            <button className="p-2 text-on-surface-variant hover:text-white rounded-full hover:bg-surface-variant/30 transition-colors" type="button" aria-label="Use microphone" disabled={isDeveloping}>
              <span className="material-symbols-outlined text-[20px]">mic</span>
            </button>
            <button
              className={`w-8 h-8 rounded-full flex items-center justify-center transition-all ${
                !prompt.trim() || !selectedProjectId || isDeveloping
                  ? 'bg-on-surface-variant/20 text-on-surface-variant/40 cursor-not-allowed'
                  : 'bg-primary text-on-primary hover:bg-opacity-90 active:scale-95'
              }`}
              disabled={!prompt.trim() || !selectedProjectId || isDeveloping}
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

        {/* Metadata Context Bar */}
        <div className="flex flex-wrap items-center gap-4 px-6 py-2 bg-surface-container-lowest border-t border-outline-variant/30">
          {/* Project selector styled exactly as context chip */}
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
            <span className="material-symbols-outlined text-[12px] absolute right-0 pointer-events-none">expand_more</span>
          </div>

          {contextItems.map((item) => (
            <button 
              className="flex items-center gap-1 text-[11px] font-label-caps text-outline hover:text-on-surface cursor-pointer transition-colors bg-transparent border-none outline-none p-0" 
              type="button" 
              key={item.label} 
              disabled={isDeveloping}
            >
              <span className="material-symbols-outlined text-[14px]">{item.icon}</span>
              <span>{item.label}</span>
              <span className="material-symbols-outlined text-[12px]">expand_more</span>
            </button>
          ))}
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
