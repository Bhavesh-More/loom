import { useEffect, useState, useRef } from 'react'

interface RippleEvent extends React.MouseEvent<HTMLButtonElement> {
  currentTarget: HTMLButtonElement
}
import PromptComposer from '../components/PromptComposer'
import Sidebar, { type AppPage } from '../components/Sidebar'
import SuggestionGrid from '../components/SuggestionGrid'
import TopAppBar from '../components/TopAppBar'
import WorkspacePanel from '../components/WorkspacePanel'
import { developProjectStream, getChatDetail, type ChatMessage } from '../lib/projects'

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
  // 1. Get user prompt from messages
  const userMsg = messages.find(m => m.role === 'user' && m.message_type === 'text')
  const prompt = userMsg?.content?.text || sessionData.title || ''

  // 2. Get project name from messages or fallback
  const startMsg = messages.find(m => m.role === 'system' && m.message_type === 'system_event' && m.content?.project_name)
  const projectName = startMsg?.content?.project_name || ''

  // 3. Process steps
  let steps: ExecutionStep[] = []
  
  // Find task plan if it exists
  const planMsg = messages.find(m => m.message_type === 'task_plan')
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
  const executionMsgs = messages.filter(m => m.message_type === 'agent_execution')
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
  }
}

function WorkspacePage({ activePage, onNavigate }: WorkspacePageProps) {
  const [activeSession, setActiveSession] = useState<ChatSession | null>(null)
  const [activeChatId, setActiveChatId] = useState<string | null>(null)
  const [followUpText, setFollowUpText] = useState('')
  const timerRef = useRef<number | null>(null)

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
    })
    try {
      const chatDetail = await getChatDetail(chatId)
      const reconstructed = reconstructSessionFromMessages(chatDetail.session, chatDetail.messages)
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
      })
    }
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

  const handleSendPrompt = async (projectId: string, promptText: string) => {
    setActiveChatId(null)
    const newSession: ChatSession = {
      projectId: projectId,
      prompt: promptText,
      projectName: '',
      status: 'planning',
      steps: [],
      elapsedTime: 0,
      workspacePath: '',
      errors: [],
    }
    setActiveSession(newSession)

    try {
      await developProjectStream(projectId, promptText, (chunk) => {
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
          } else if (chunk.type === 'complete') {
            updated.steps = updated.steps.map(s => s.status === 'running' || s.status === 'pending' ? { ...s, status: 'completed' } : s)
            updated.status = 'completed'
          } else if (chunk.type === 'error') {
            updated.errors = [...updated.errors, chunk.message]
            updated.status = 'failed'
          }

          return updated
        })
      })
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
      />

      {/* Main Content Pane */}
      <main className="flex-1 flex flex-col h-full bg-[#101010] relative overflow-hidden">
        {/* Dynamic Top Header */}
        <TopAppBar 
          projectName={activeSession?.projectName} 
          prompt={activeSession?.prompt} 
          isSessionActive={!!activeSession} 
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
              <div className="absolute bottom-6 left-1/2 -translate-x-1/2 w-full max-w-2xl px-6 z-10 flex flex-col items-center">
                <div className="w-full bg-[#171717] border border-[#262626] rounded-xl flex flex-col shadow-2xl">
                  <input
                    className="w-full bg-transparent border-none text-primary placeholder-on-surface-variant/40 px-4 py-4 focus:ring-0 focus:border-transparent outline-none text-[16px] leading-tight"
                    value={followUpText}
                    onChange={(e) => setFollowUpText(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault()
                        setFollowUpText('') // Clear locally, do not submit to backend
                      }
                    }}
                    placeholder="Ask for follow-up changes"
                    type="text"
                  />
                  <div className="flex justify-between items-center px-4 pb-3">
                    <div className="flex items-center gap-2">
                      <button className="p-1.5 text-on-surface-variant hover:text-white rounded hover:bg-[#262626] transition-colors" type="button" aria-label="Add attachment">
                        <span className="material-symbols-outlined text-[20px]">add</span>
                      </button>
                      {/* Task 2: Permission select with auto-review and Full Access options */}
                      <div className="relative">
                        <select className="flex items-center gap-1.5 text-[12px] text-on-surface-variant hover:text-white px-2.5 py-1 rounded border border-outline-variant/30 hover:bg-[#262626] transition-colors cursor-pointer appearance-none bg-[#171717]">
                          <option value="auto-review">Auto-review</option>
                          <option value="full-access">Full Access</option>
                        </select>
                        <span className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none text-[16px] text-on-surface-variant">keyboard_arrow_down</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      {/* Task 3: Model selector */}
                      <div className="relative">
                        <select className="text-[12px] text-on-surface-variant font-code-md bg-[#171717] border border-outline-variant/30 rounded px-2 py-1 cursor-pointer appearance-none hover:text-white hover:border-primary">
                          <option value="5.5">5.5 <span className="opacity-50">High</span></option>
                          <option value="4.0">4.0 <span className="opacity-50">Medium</span></option>
                          <option value="3.5">3.5 <span className="opacity-50">Low</span></option>
                        </select>
                        <span className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none text-[14px] text-on-surface-variant">keyboard_arrow_down</span>
                      </div>
                      {/* Task 3: Agent selector */}
                      <div className="relative">
                        <select className="text-[12px] text-on-surface-variant font-code-md bg-[#171717] border border-outline-variant/30 rounded px-2 py-1 cursor-pointer appearance-none hover:text-white hover:border-primary">
                          <option value="dev-agent">Dev Agent</option>
                          <option value="review-agent">Review Agent</option>
                          <option value="qa-agent">QA Agent</option>
                        </select>
                        <span className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none text-[14px] text-on-surface-variant">keyboard_arrow_down</span>
                      </div>
                      {/* Task 4: Submit button with ripple effect */}
                      <button
                        onClick={(e) => {
                          createRipple(e)
                          setFollowUpText('')
                        }}
                        className={`w-8 h-8 rounded flex items-center justify-center transition-all ${
                          followUpText.trim()
                            ? 'bg-primary text-on-primary hover:bg-opacity-90 active:scale-95 cursor-pointer'
                            : 'bg-[#353534] text-on-surface-variant opacity-50 cursor-not-allowed'
                        }`}
                        type="button"
                        aria-label="Submit follow-up"
                      >
                        <span className="material-symbols-outlined text-[20px]">arrow_upward</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Workspace File Explorer & Code Editor Panel */}
            {activeSession.workspacePath && activeSession.projectId && (
              <div className="w-[55%] h-full shrink-0 animate-step-fade-in z-20">
                <WorkspacePanel
                  projectId={activeSession.projectId}
                  projectName={activeSession.projectName}
                />
              </div>
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
