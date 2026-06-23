import { useEffect, useState, useRef } from 'react'
import PromptComposer from '../components/PromptComposer'
import Sidebar, { type AppPage } from '../components/Sidebar'
import SuggestionGrid from '../components/SuggestionGrid'
import TopAppBar from '../components/TopAppBar'
import WorkspacePanel from '../components/WorkspacePanel'
import { developProjectStream, getChatDetail, type ChatMessage } from '../lib/projects'
import { getDownloadedAgents, type AgentData } from '../lib/agents'

type WorkspacePageProps = {
  activePage: AppPage
  onNavigate: (page: AppPage) => void
}

type ExecutionStep = {
  step: number
  agent: string
  task: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  files: string[]
}

type ChatSession = {
  projectId?: string
  prompt: string
  projectName: string
  status: 'idle' | 'planning' | 'running' | 'completed' | 'failed'
  steps: ExecutionStep[]
  elapsedTime: number
  workspacePath: string
  errors: string[]
  selectedAgentIds: string[]
  contextFiles: string[]
  qaResponse?: string
}


function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`
}

function getFileIcon(filename: string): string {
  if (filename.endsWith('.py')) return 'code'
  if (filename.endsWith('.sql')) return 'database'
  if (filename.endsWith('.yml') || filename.endsWith('.yaml')) return 'settings'
  if (filename.endsWith('.md')) return 'description'
  if (filename.endsWith('.txt')) return 'description'
  if (filename.endsWith('.js') || filename.endsWith('.ts') || filename.endsWith('.tsx') || filename.endsWith('.jsx')) return 'code'
  return 'description'
}

function getFileColorClass(filename: string): string {
  if (filename.endsWith('.py')) return 'text-primary'
  if (filename.endsWith('.sql')) return 'text-secondary'
  if (filename.endsWith('.yml') || filename.endsWith('.yaml')) return 'text-on-surface-variant'
  if (filename.endsWith('.md')) return 'text-secondary'
  if (filename.endsWith('.js') || filename.endsWith('.ts') || filename.endsWith('.tsx') || filename.endsWith('.jsx')) return 'text-[#61DAFB]'
  return 'text-on-surface-variant'
}

function reconstructSessionFromMessages(sessionData: any, messages: ChatMessage[]): ChatSession {
  const latestUserIndex = findLastIndex(messages, (m) => m.role === 'user' && m.message_type === 'text')
  const latestPlanIndex = findLastIndex(messages, (m) => m.message_type === 'task_plan')

  // 1. Get the latest user prompt from messages
  const userMsg = latestUserIndex >= 0 ? messages[latestUserIndex] : undefined
  const prompt = userMsg?.content?.text || sessionData.title || ''

  // 2. Get project name from messages or fallback
  const startMsg = messages.find(m => m.role === 'system' && m.message_type === 'system_event' && m.content?.project_name)
  const projectName = startMsg?.content?.project_name || ''

  // 3. Process steps
  let steps: ExecutionStep[] = []
  
  // Find task plan if it exists
  const planMsg = latestPlanIndex >= 0 ? messages[latestPlanIndex] : undefined
  if (planMsg && planMsg.content?.plan) {
    steps = planMsg.content.plan.map((step: any, idx: number) => ({
      step: step.step || idx + 1,
      agent: step.agent || 'Unknown',
      task: step.task || '',
      status: 'pending',
      files: [],
    }))
  }

  // Apply agent execution updates
  const executionMsgs = messages.filter((m, index) =>
    m.message_type === 'agent_execution' && index > latestPlanIndex
  )
  executionMsgs.forEach(m => {
    const completedIdx = m.content?.completed_step_idx
    if (completedIdx !== undefined && steps[completedIdx]) {
      const stepErrors = m.content?.errors || []
      steps[completedIdx].status = stepErrors.length > 0 ? 'failed' : 'completed'
      steps[completedIdx].files = m.content?.files || []
    }
  })

  // 4. Get workspace path
  const fileWriterMsg = messages.find(m => m.message_type === 'system_event' && m.content?.workspace_path)
  const workspacePath = fileWriterMsg?.content?.workspace_path || ''

  // 5. Gather all errors
  const errors: string[] = []
  messages.forEach(m => {
    if (m.content?.errors) {
      errors.push(...m.content.errors)
    }
  })

  // 6. Status of the session
  let status: ChatSession['status'] = 'completed'
  // If there's an error message or the execution failed, mark failed
  const errorMsg = messages.find(m => m.message_type === 'system_event' && m.content?.text?.includes('failed'))
  if (errorMsg || errors.length > 0) {
    status = 'failed'
  }

  // 6.5. Get QA response from messages if it exists
  const qaMsg = messages.find(m => m.role === 'assistant' && m.message_type === 'text')
  const qaResponse = qaMsg?.content?.text || ''

  // 7. Calculate elapsed time if possible
  let elapsedTime = 0
  if (messages.length > 1) {
    const firstTime = new Date(messages[0].created_at).getTime()
    const lastTime = new Date(messages[messages.length - 1].created_at).getTime()
    elapsedTime = Math.max(0, Math.floor((lastTime - firstTime) / 1000))
  }

  return {
    projectId: sessionData.project_id,
    prompt,
    projectName,
    status,
    steps,
    elapsedTime,
    workspacePath,
    errors,
    selectedAgentIds: [],
    contextFiles: [],
    qaResponse,
  }
}

function findLastIndex<T>(items: T[], predicate: (item: T, index: number) => boolean): number {
  for (let index = items.length - 1; index >= 0; index -= 1) {
    if (predicate(items[index], index)) {
      return index
    }
  }
  return -1
}

function WorkspacePage({ activePage, onNavigate }: WorkspacePageProps) {
  const [activeSession, setActiveSession] = useState<ChatSession | null>(null)
  const [activeChatId, setActiveChatId] = useState<string | null>(null)
  const [followUpText, setFollowUpText] = useState('')
  const [followUpPermission, setFollowUpPermission] = useState('auto-review')
  const [followUpModel, setFollowUpModel] = useState('llama-3.3-70b')
  const [isWorkspaceOpen, setIsWorkspaceOpen] = useState(true)
  const timerRef = useRef<number | null>(null)

  const [downloadedAgents, setDownloadedAgents] = useState<AgentData[]>([])
  const [followUpSelectedAgents, setFollowUpSelectedAgents] = useState<string[]>([])
  const [isAgentDropdownOpen, setIsAgentDropdownOpen] = useState(false)
  const agentDropdownRef = useRef<HTMLDivElement>(null)

  // Load downloaded agents on mount
  useEffect(() => {
    async function loadAgents() {
      try {
        const data = await getDownloadedAgents()
        setDownloadedAgents(data)
      } catch (err) {
        console.error("Failed to load agents in WorkspacePage", err)
      }
    }
    void loadAgents()
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

  // Sync selected agents when activeSession changes
  useEffect(() => {
    if (activeSession) {
      setFollowUpSelectedAgents(activeSession.selectedAgentIds || [])
    } else {
      setFollowUpSelectedAgents([])
    }
  }, [activeSession?.projectId, activeSession?.selectedAgentIds])

  // Task 4: Ripple effect helper
  const createRipple = (e: React.MouseEvent<HTMLButtonElement>) => {
    const button = e.currentTarget
    const ripple = document.createElement('span')
    const rect = button.getBoundingClientRect()
    const size = Math.max(rect.width, rect.height)
    const x = e.clientX - rect.left - size / 2
    const y = e.clientY - rect.top - size / 2

    ripple.style.width = ripple.style.height = `${size}px`
    ripple.style.left = `${x}px`
    ripple.style.top = `${y}px`
    ripple.style.borderRadius = '50%'
    ripple.style.position = 'absolute'
    ripple.style.backgroundColor = 'rgba(255, 255, 255, 0.4)'
    ripple.style.transform = 'scale(0)'
    ripple.style.animation = 'rippleAnimation 0.6s ease-out'
    ripple.style.pointerEvents = 'none'

    button.appendChild(ripple)
    setTimeout(() => ripple.remove(), 600)
  }

  const handleSelectChat = async (chatId: string) => {
    setActiveChatId(chatId)
    // Create a temporary loading state
    setActiveSession({
      prompt: 'Loading chat session...',
      projectName: '',
      status: 'planning',
      steps: [],
      elapsedTime: 0,
      workspacePath: '',
      errors: [],
      selectedAgentIds: [],
      contextFiles: [],
    })
    try {
      const chatDetail = await getChatDetail(chatId)
      const reconstructed = reconstructSessionFromMessages(chatDetail.session, chatDetail.messages)
      if (reconstructed.projectId) {
        try {
          const projectResponse = await fetch(`${import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'}/projects/${reconstructed.projectId}`)
          if (projectResponse.ok) {
            const projectData = await projectResponse.json()
            reconstructed.selectedAgentIds = projectData.agent_ids || []
          }
        } catch (err) {
          console.error("Failed to load project agents for chat detail", err)
        }
      }
      setActiveSession(reconstructed)
    } catch (err: any) {
      console.error("Failed to load chat details", err)
      setActiveSession({
        prompt: 'Error loading chat',
        projectName: '',
        status: 'failed',
        steps: [],
        elapsedTime: 0,
        workspacePath: '',
        errors: [`Failed to retrieve chat history: ${err.message || 'Unknown error'}`],
        selectedAgentIds: [],
        contextFiles: [],
      })
    }
  }

  const handleSelectProject = (projectId: string, projectName: string) => {
    setActiveChatId(null)
    setActiveSession({
      projectId: projectId,
      prompt: '',
      projectName: projectName,
      status: 'idle',
      steps: [],
      elapsedTime: 0,
      workspacePath: '',
      errors: [],
      selectedAgentIds: [],
      contextFiles: [],
    })
    setIsWorkspaceOpen(true)
  }

  // Start incrementing timer when session is running
  useEffect(() => {
    if (activeSession && (activeSession.status === 'planning' || activeSession.status === 'running')) {
      if (!timerRef.current) {
        timerRef.current = window.setInterval(() => {
          setActiveSession((curr) => {
            if (!curr) return null
            return {
              ...curr,
              elapsedTime: curr.elapsedTime + 1,
            }
          })
        }, 1000)
      }
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current)
        timerRef.current = null
      }
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current)
        timerRef.current = null
      }
    }
  }, [activeSession?.status])

  const runPrompt = async (
    projectId: string,
    promptText: string,
    selectedAgentIds: string[],
    chatSessionId?: string | null
  ) => {
    if (!chatSessionId) {
      setActiveChatId(null)
    }
    const newSession: ChatSession = {
      projectId: projectId,
      prompt: promptText,
      projectName: activeSession?.projectId === projectId ? activeSession.projectName : '',
      status: 'planning',
      steps: [],
      elapsedTime: 0,
      workspacePath: activeSession?.projectId === projectId ? activeSession.workspacePath : '',
      errors: [],
      selectedAgentIds,
      contextFiles: [],
    }
    setActiveSession(newSession)
    setIsWorkspaceOpen(true)

    try {
      await developProjectStream(projectId, promptText, selectedAgentIds, (chunk) => {
        if (chunk.type === 'start') {
          if (chunk.chat_id) {
            setActiveChatId(chunk.chat_id)
          }
          window.dispatchEvent(new CustomEvent('chat-created'))
        } else if (chunk.type === 'complete' || chunk.type === 'error') {
          setTimeout(() => {
            window.dispatchEvent(new CustomEvent('chat-created'))
          }, 200)
        }

        setActiveSession((curr) => {
          if (!curr) return null
          
          const updated = { ...curr }

          if (chunk.type === 'start') {
            updated.projectName = chunk.project_name || ''
            updated.status = 'planning'
          } else if (chunk.type === 'context') {
            if (chunk.errors && chunk.errors.length > 0) {
              updated.errors = [...updated.errors, ...chunk.errors]
            }
          } else if (chunk.type === 'planner') {
            const planSteps = chunk.plan || []
            updated.steps = planSteps.map((step: any, idx: number) => ({
              step: step.step || idx + 1,
              agent: step.agent || 'Unknown',
              task: step.task || '',
              status: idx === 0 ? 'running' : 'pending',
              files: [],
            }))
            updated.status = 'running'
          } else if (chunk.type === 'executor') {
            const completedIdx = chunk.completed_step_idx
            
            // Mark completed step
            if (updated.steps[completedIdx]) {
              updated.steps[completedIdx].status = chunk.errors && chunk.errors.length > 0 ? 'failed' : 'completed'
              updated.steps[completedIdx].files = chunk.files || []
            }
            
            // Mark next step as running
            if (updated.steps[completedIdx + 1]) {
              updated.steps[completedIdx + 1].status = 'running'
            }

            if (chunk.errors && chunk.errors.length > 0) {
              updated.errors = [...updated.errors, ...chunk.errors]
            }
          } else if (chunk.type === 'file_writer') {
            updated.workspacePath = chunk.workspace_path || ''
            if (chunk.errors && chunk.errors.length > 0) {
              updated.errors = [...updated.errors, ...chunk.errors]
            }
          } else if (chunk.type === 'qa') {
            updated.qaResponse = chunk.message || ''
          } else if (chunk.type === 'complete') {
            updated.steps = updated.steps.map(s => s.status === 'running' || s.status === 'pending' ? { ...s, status: 'completed' } : s)
            updated.status = 'completed'
          } else if (chunk.type === 'error') {
            updated.errors = [...updated.errors, chunk.message]
            updated.status = 'failed'
          }

          return updated
        })
      }, chatSessionId)
    } catch (err: any) {
      setActiveSession((curr) => {
        if (!curr) return null
        return {
          ...curr,
          status: 'failed',
          errors: [...curr.errors, err.message || 'Stream connection error'],
        }
      })
    }
  }

  const handleSendPrompt = async (
    projectId: string,
    promptText: string,
    selectedAgentIds: string[]
  ) => {
    await runPrompt(projectId, promptText, selectedAgentIds)
  }

  const handleSendFollowUp = async () => {
    const promptText = followUpText.trim()
    if (!promptText || isDeveloping || !activeSession?.projectId) {
      return
    }
    const projectId = activeSession.projectId
    const agentIds = followUpSelectedAgents.length > 0 ? followUpSelectedAgents : (activeSession.selectedAgentIds || [])
    setFollowUpText('')
    await runPrompt(projectId, promptText, agentIds, activeChatId)
  }

  const isDeveloping = activeSession 
    ? (activeSession.status === 'planning' || activeSession.status === 'running')
    : false

  return (
    <div className="h-screen w-full flex overflow-hidden ">
      {/* Sidebar Component */}
      <Sidebar 
        activePage={activePage} 
        onNavigate={(page) => {
          if (page === 'chat') {
            setActiveSession(null)
            setActiveChatId(null)
          }
          onNavigate(page)
        }} 
        activeChatId={activeChatId}
        onSelectChat={handleSelectChat}
        onSelectProject={handleSelectProject}
      />

      {/* Main Content Pane */}
      <main className="flex-1 flex flex-col h-full bg-[#101010] relative overflow-hidden">
        {/* Dynamic Top Header */}
        <TopAppBar 
          projectName={activeSession?.projectName} 
          prompt={activeSession?.prompt} 
          isSessionActive={!!activeSession} 
          isWorkspaceOpen={isWorkspaceOpen}
          onToggleWorkspace={() => setIsWorkspaceOpen((open) => !open)}
        />

        {activeSession ? (
          /* Active session layout matching reference-chat-middle.html */
          <div className="flex-1 flex overflow-hidden pt-14">
            
            {/* Left Canvas (Chat & Logs + Input Box) */}
            <div className="flex-1 flex flex-col relative h-full min-w-0">
              {/* Scrollable Chat Feed */}
              <div className="flex-1 flex flex-col overflow-y-auto scroll-smooth pb-44 hide-scrollbar">
                <div className="max-w-3xl mx-auto w-full px-6 py-8 flex flex-col gap-8">
                  
                  {/* User Prompt Card */}
                  {/* <div className="glass-panel p-6 rounded-xl flex gap-4 border border-[#262626] animate-step-fade-in">
                    <div className="w-8 h-8 rounded-full bg-surface-variant flex items-center justify-center shrink-0">
                      <span className="material-symbols-outlined text-[18px] text-on-surface-variant">person</span>
                    </div>
                    <div className="font-body-sm text-body-sm text-on-surface leading-relaxed whitespace-pre-wrap flex-1">
                      {activeSession.prompt}
                    </div>
                  </div> */}

                  {/* AI Agent Activity Feed */}
                  <div className="flex flex-col gap-6 ml-2">
                    
                    {/* Status Header */}
                    <div className="flex items-center gap-3 text-on-surface-variant font-code-md text-[12px] animate-step-fade-in" style={{ animationDelay: '0.1s' }}>
                      <span className={`material-symbols-outlined text-[16px] ${isDeveloping ? 'animate-spin' : ''}`}>
                        {isDeveloping ? 'progress_activity' : 'schedule'}
                      </span>
                      <span>
                        {activeSession.status === 'completed'
                          ? `Worked for ${formatTime(activeSession.elapsedTime)}`
                          : activeSession.status === 'failed'
                            ? `Stopped after ${formatTime(activeSession.elapsedTime)}`
                            : `Working... (${formatTime(activeSession.elapsedTime)})`
                        }
                      </span>
                      <span className="material-symbols-outlined text-[16px]">chevron_right</span>
                    </div>

                    {/* Activity Log */}
                    <div className="flex flex-col gap-4 font-body-sm text-body-sm">
                      <p className="text-primary font-medium animate-step-fade-in" style={{ animationDelay: '0.15s' }}>
                        {activeSession.status === 'planning' && 'Formulating multi-agent build plan...'}
                        {activeSession.status === 'running' && 'Executing step-by-step developer graph...'}
                        {activeSession.status === 'completed' && `Successfully completed project ${activeSession.projectName}!`}
                        {activeSession.status === 'failed' && 'Development execution halted due to errors.'}
                      </p>

                      {activeSession.qaResponse && (
                        <div className="glass-panel p-6 rounded-xl border border-outline-variant/30 bg-[#161616]/50 animate-step-fade-in text-[14px] leading-relaxed text-on-surface whitespace-pre-wrap">
                          {activeSession.qaResponse}
                        </div>
                      )}

                      {activeSession.steps.length > 0 ? (
                        <ul className="flex flex-col gap-4 pl-1">
                          {activeSession.steps.map((step, idx) => {
                            let bulletColor = 'bg-[#404040]'
                            if (step.status === 'completed') bulletColor = 'bg-tertiary-fixed-dim'
                            else if (step.status === 'failed') bulletColor = 'bg-[#ef4444]'
                            else if (step.status === 'running') bulletColor = 'bg-secondary-container pulse-glow ring-2 ring-secondary-container/20'

                            return (
                              <li 
                                key={idx} 
                                className="flex gap-3 animate-step-fade-in"
                                style={{ animationDelay: `${0.2 + idx * 0.08}s` }}
                              >
                                <div className={`mt-2 w-1.5 h-1.5 rounded-full shrink-0 ${bulletColor}`} />
                                <div className="flex flex-col gap-1.5 flex-1">
                                  <div className="flex items-center gap-2">
                                    <span className="text-primary font-medium">
                                      {step.agent.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())} Agent
                                    </span>
                                    {step.status === 'running' && (
                                      <span className="text-[11px] font-label-caps bg-secondary-container/20 text-secondary px-2 py-0.5 rounded-full animate-pulse">
                                        active
                                      </span>
                                    )}
                                    {step.status === 'completed' && (
                                      <span className="material-symbols-outlined text-[16px] text-tertiary-fixed-dim">check_circle</span>
                                    )}
                                  </div>
                                  <div className="text-on-surface-variant text-[13px] leading-relaxed">{step.task}</div>

                                  {/* Generated File list under the completed step */}
                                  {step.files && step.files.length > 0 && (
                                    <div className="flex flex-col gap-1.5 pl-4 border-l border-[#262626] mt-2">
                                      {step.files.map((file, fileIdx) => (
                                        <div 
                                          key={fileIdx} 
                                          className="flex items-center gap-2 animate-file-slide-in"
                                          style={{ animationDelay: `${0.15 + fileIdx * 0.05}s` }}
                                        >
                                          <span className={`material-symbols-outlined text-[14px] ${getFileColorClass(file)}`}>
                                            {getFileIcon(file)}
                                          </span>
                                          <span className="font-code-md text-[13px] text-secondary">
                                            {file}
                                          </span>
                                        </div>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              </li>
                            )
                          })}
                        </ul>
                      ) : (
                        activeSession.status === 'planning' && (
                          <div className="flex items-center gap-2 text-on-surface-variant font-code-md text-[13px] animate-pulse">
                            <span className="material-symbols-outlined animate-spin text-[16px]">sync</span>
                            <span>Consulting planner agent...</span>
                          </div>
                        )
                      )}

                      {/* Workspace Path Success Panel */}
                      {activeSession.workspacePath && (
                        <div className="mt-4 glass-panel p-4 rounded-xl flex items-center justify-between border-[#262626] animate-step-fade-in" style={{ animationDelay: '0.4s' }}>
                          <div className="flex items-center gap-3 font-code-md text-[13px]">
                            <span className="material-symbols-outlined text-tertiary-fixed-dim text-[18px]">folder_open</span>
                            <span className="text-on-surface-variant">Workspace folder generated: <strong className="text-primary font-medium">{activeSession.workspacePath}</strong></span>
                          </div>
                        </div>
                      )}

                      {/* Errors Panel */}
                      {activeSession.errors && activeSession.errors.length > 0 && (
                        <div className="mt-4 glass-panel p-4 rounded-xl border-[#ef4444]/20 bg-[#ef4444]/5 animate-step-fade-in" style={{ animationDelay: '0.4s' }}>
                          <div className="flex items-center gap-2 text-[#ef4444] font-semibold text-[14px] mb-2">
                            <span className="material-symbols-outlined">error</span>
                            <span>Errors encountered during execution:</span>
                          </div>
                          <ul className="list-disc pl-5 text-[13px] text-[#ef4444]/80 flex flex-col gap-1">
                            {activeSession.errors.map((err, errIdx) => (
                              <li key={errIdx}>{err}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Sticky Chat Input Box at the Bottom of Left Pane */}
              <div className="absolute bottom-6 left-0 right-0 z-10 flex justify-center px-5 pointer-events-none">
                <div className="w-full max-w-[820px] bg-[#171717] border border-[#2c2c2c] rounded-[22px] flex flex-col shadow-2xl overflow-hidden pointer-events-auto">
                  <textarea
                    className="block w-full min-h-[82px] max-h-36 bg-transparent border-none text-primary placeholder-on-surface-variant/45 px-5 pt-4 pb-2 focus:ring-0 focus:border-transparent outline-none text-[15px] leading-relaxed resize-none"
                    value={followUpText}
                    onChange={(e) => setFollowUpText(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault()
                        void handleSendFollowUp()
                      }
                    }}
                    placeholder="Ask for follow-up changes"
                    rows={2}
                    disabled={isDeveloping}
                  />
                  <div className="flex flex-wrap items-center justify-between px-4 pb-3 gap-2">
                    <div className="flex flex-wrap items-center gap-2 min-w-0">
                      <button className="w-8 h-8 shrink-0 flex items-center justify-center text-on-surface-variant hover:text-white rounded-lg hover:bg-[#262626] transition-colors" type="button" aria-label="Add attachment">
                        <span className="material-symbols-outlined text-[20px]">add</span>
                      </button>
                      <div className="relative shrink-0">
                        <select
                          className="h-9 text-[12px] text-on-surface-variant hover:text-white pl-3 pr-8 rounded-lg border border-outline-variant/30 hover:bg-[#262626] transition-colors cursor-pointer appearance-none bg-[#171717]"
                          value={followUpPermission}
                          onChange={(e) => setFollowUpPermission(e.target.value)}
                          disabled={isDeveloping}
                        >
                          <option value="auto-review">Auto-review</option>
                          <option value="full-access">Full Access</option>
                          <option value="default">Default</option>
                        </select>
                        <span className="material-symbols-outlined absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none text-[16px] text-on-surface-variant">keyboard_arrow_down</span>
                      </div>
                      <div className="h-9 flex items-center gap-1.5 text-[12px] text-on-surface-variant px-3 rounded-lg border border-outline-variant/30 bg-[#171717] min-w-[150px] max-w-[240px]">
                        <span className="material-symbols-outlined text-[15px]">folder</span>
                        <span className="truncate">{activeSession.projectName || 'Selected project'}</span>
                      </div>
                    </div>
                    <div className="flex flex-wrap items-center justify-end gap-2 min-w-0">
                      <div className="relative shrink-0">
                        <select
                          className="h-9 text-[12px] text-on-surface-variant font-code-md bg-[#171717] border border-outline-variant/30 rounded-lg pl-3 pr-8 cursor-pointer appearance-none hover:text-white hover:border-primary"
                          value={followUpModel}
                          onChange={(e) => setFollowUpModel(e.target.value)}
                          disabled={isDeveloping}
                        >
                          <option value="llama-3.3-70b">Llama 3.3</option>
                          <option value="qwen3-32b">Qwen 3</option>
                          <option value="default">Default</option>
                        </select>
                        <span className="material-symbols-outlined absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none text-[14px] text-on-surface-variant">keyboard_arrow_down</span>
                      </div>
                      {/* Agent Selector (Multi-select) */}
                      <div ref={agentDropdownRef} className="relative shrink-0">
                        <button
                          className="h-9 flex items-center gap-2 px-3 text-on-surface-variant hover:text-white rounded-lg border border-outline-variant/30 hover:bg-[#262626] transition-colors cursor-pointer text-left bg-[#171717] max-w-[150px]"
                          type="button"
                          onClick={() => setIsAgentDropdownOpen(!isAgentDropdownOpen)}
                          disabled={isDeveloping}
                        >
                          <div className="flex -space-x-1.5 pointer-events-none" aria-hidden="true">
                            {followUpSelectedAgents.map((agentId) => {
                              const agent = downloadedAgents.find((a) => a.id === agentId)
                              if (!agent) return null
                              return (
                                <div key={agent.id} className="w-4 h-4 rounded bg-surface-container-highest flex items-center justify-center border border-background">
                                  <span className="material-symbols-outlined text-[10px]">{agent.icon}</span> 
                                </div>
                              )
                            })}
                          </div>
                          <span className="font-code-md text-[12px] truncate">
                            {followUpSelectedAgents.length === 0
                              ? 'No Agents'
                              : followUpSelectedAgents.length === 1
                              ? downloadedAgents.find((a) => a.id === followUpSelectedAgents[0])?.name
                              : 'Agents'}
                          </span>
                          {followUpSelectedAgents.length > 2 && (
                            <span className="text-[10px] bg-secondary-container/20 text-secondary px-1.5 rounded-full">
                              +{followUpSelectedAgents.length - 2}
                            </span>
                          )}
                          <span className="material-symbols-outlined text-[14px] shrink-0">keyboard_arrow_down</span>
                        </button>

                        {isAgentDropdownOpen && (
                          <div className="absolute right-0 bottom-full mb-2 z-50 min-w-[200px] bg-[#171717] border border-outline-variant/30 rounded-lg p-2 shadow-xl flex flex-col gap-1">
                            {downloadedAgents.length === 0 ? (
                              <div className="px-3 py-2 text-[12px] text-on-surface-variant">
                                Download agents from Marketplace first.
                              </div>
                            ) : downloadedAgents.map((agent) => {
                              const isSelected = followUpSelectedAgents.includes(agent.id)
                              return (
                                <div
                                  key={agent.id}
                                  className="flex items-center gap-2 px-3 py-2 hover:bg-[#262626] rounded-md cursor-pointer text-on-surface select-none text-[12px]"
                                  onClick={() => {
                                    if (isSelected) {
                                      setFollowUpSelectedAgents(followUpSelectedAgents.filter((id) => id !== agent.id))
                                    } else {
                                      setFollowUpSelectedAgents([...followUpSelectedAgents, agent.id])
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
                      <button
                        onClick={(e) => {
                          createRipple(e)
                          void handleSendFollowUp()
                        }}
                        className={`w-9 h-9 rounded-lg flex items-center justify-center transition-all shrink-0 overflow-hidden ${
                          followUpText.trim()
                            ? 'bg-primary text-on-primary hover:bg-opacity-90 active:scale-95 cursor-pointer'
                            : 'bg-[#353534] text-on-surface-variant opacity-50 cursor-not-allowed'
                        }`}
                        type="button"
                        aria-label="Submit follow-up"
                        disabled={!followUpText.trim() || isDeveloping}
                      >
                        <span className="material-symbols-outlined text-[20px]">
                          {isDeveloping ? 'progress_activity' : 'arrow_upward'}
                        </span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Workspace File Explorer & Code Editor Panel */}
            {activeSession.projectId && isWorkspaceOpen && (
              <div className="w-[55%] h-full shrink-0 animate-step-fade-in z-20">
                <WorkspacePanel
                  projectId={activeSession.projectId}
                  projectName={activeSession.projectName}
                  onClose={() => setIsWorkspaceOpen(false)}
                  status={activeSession.status}
                />
              </div>
            )}

            {activeSession.projectId && !isWorkspaceOpen && (
              <button
                type="button"
                onClick={() => setIsWorkspaceOpen(true)}
                className="absolute right-4 top-20 z-30 flex items-center gap-2 bg-[#171717] border border-[#262626] text-on-surface-variant hover:text-white rounded-lg px-3 py-2 shadow-xl transition-colors"
                aria-label="Show workspace explorer"
              >
                <span className="material-symbols-outlined text-[18px]">view_sidebar</span>
                <span className="text-[12px] font-code-md">Files</span>
              </button>
            )}

          </div>
        ) : (
          /* Idle landing view matching reference.html */
          <div className="flex-1 flex flex-col items-center justify-center px-6 relative z-10 w-full max-w-5xl mx-auto pt-14">
            
            {/* Main Title */}
            <h1 className="font-headline-lg text-headline-lg text-white mb-12 text-center max-w-2xl text-[32px] font-bold tracking-tight animate-step-fade-in" style={{ animationDelay: '0.1s' }}>
              What should we build in L00m?
            </h1>

            {/* Central Controls Container */}
            <div className="w-full max-w-5xl space-y-4 animate-step-fade-in" style={{ animationDelay: '0.2s' }}>
              {/* Prompt Composer */}
              <PromptComposer onSendPrompt={handleSendPrompt} isDevelopingProps={isDeveloping} />
            </div>

            {/* Suggestion Grid */}
            <div className="animate-step-fade-in w-full flex justify-center" style={{ animationDelay: '0.3s' }}>
              <SuggestionGrid />
            </div>

            {/* Atmospheric background glows */}
            <div className="absolute inset-0 pointer-events-none overflow-hidden opacity-20 z-0 select-none">
              <div className="absolute -top-1/4 -right-1/4 w-[800px] h-[800px] bg-secondary-container blur-[160px] rounded-full opacity-10" />
              <div className="absolute -bottom-1/4 -left-1/4 w-[600px] h-[600px] bg-primary-container blur-[160px] rounded-full opacity-5" />
            </div>

          </div>
        )}
      </main>
    </div>
  )
}

export default WorkspacePage
