import { useEffect, useState, useRef } from 'react'
import PromptComposer from '../components/PromptComposer'
import Sidebar, { type AppPage } from '../components/Sidebar'
import SuggestionGrid from '../components/SuggestionGrid'
import TopAppBar from '../components/TopAppBar'
import { developProjectStream } from '../lib/projects'

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

function WorkspacePage({ activePage, onNavigate }: WorkspacePageProps) {
  const [activeSession, setActiveSession] = useState<ChatSession | null>(null)
  const [followUpText, setFollowUpText] = useState('')
  const timerRef = useRef<number | null>(null)

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
    const newSession: ChatSession = {
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
    <div className="h-screen w-full flex overflow-hidden bg-background">
      {/* Sidebar Component */}
      <Sidebar 
        activePage={activePage} 
        onNavigate={(page) => {
          if (page === 'chat') {
            setActiveSession(null)
          }
          onNavigate(page)
        }} 
      />

      {/* Main Content Pane */}
      <main className="flex-1 flex flex-col h-full bg-[#000000] relative overflow-hidden">
        {/* Dynamic Top Header */}
        <TopAppBar 
          projectName={activeSession?.projectName} 
          prompt={activeSession?.prompt} 
          isSessionActive={!!activeSession} 
        />

        {activeSession ? (
          /* Active session layout matching reference-chat-middle.html */
          <div className="flex-1 flex overflow-hidden pt-14">
            
            {/* Center Canvas (Chat & Logs) */}
            <div className="flex-1 flex flex-col overflow-y-auto scroll-smooth pb-44 hide-scrollbar">
              <div className="max-w-5xl mx-auto w-full px-6 py-8 flex flex-col gap-8">
                
                {/* User Prompt Card */}
                <div className="glass-panel p-6 rounded-xl flex gap-4 border border-[#262626] animate-step-fade-in">
                  <div className="w-8 h-8 rounded-full bg-surface-variant flex items-center justify-center shrink-0">
                    <span className="material-symbols-outlined text-[18px] text-on-surface-variant">person</span>
                  </div>
                  <div className="font-body-sm text-body-sm text-on-surface leading-relaxed whitespace-pre-wrap flex-1">
                    {activeSession.prompt}
                  </div>
                </div>

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



            {/* Sticky Chat Input Box at the Bottom */}
            <div className="absolute bottom-6 left-1/2 -translate-x-1/2 w-full max-w-5xl px-6 z-10 flex flex-col items-center">
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
                    <button className="flex items-center gap-1.5 text-[12px] text-on-surface-variant hover:text-white px-2.5 py-1 rounded border border-outline-variant/30 hover:bg-[#262626] transition-colors" type="button">
                      <span className="material-symbols-outlined text-[16px]">pan_tool</span>
                      <span>Default permissions</span>
                      <span className="material-symbols-outlined text-[16px]">keyboard_arrow_down</span>
                    </button>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-[12px] text-on-surface-variant font-code-md">
                      5.5 <span className="opacity-50">High</span> <span className="material-symbols-outlined text-[14px] align-middle">keyboard_arrow_down</span>
                    </span>
                    <button className="p-1.5 text-on-surface-variant hover:text-white rounded hover:bg-[#262626] transition-colors" type="button" aria-label="Use mic">
                      <span className="material-symbols-outlined text-[20px]">mic</span>
                    </button>
                    <button 
                      onClick={() => setFollowUpText('')}
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
