import { type ChangeEvent, useEffect, useRef, useState } from 'react'
import { getProjects, type Project } from '../lib/projects'
import MaterialIcon from './MaterialIcon'

const contextItems = [
  { label: 'Work locally', icon: 'laptop_windows' },
  { label: 'main', icon: 'account_tree' },
]

function PromptComposer() {
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const [prompt, setPrompt] = useState('')
  const [projects, setProjects] = useState<Project[]>([])
  const [selectedProjectId, setSelectedProjectId] = useState('')

  const handleChange = (event: ChangeEvent<HTMLTextAreaElement>) => {
    setPrompt(event.target.value)

    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = `${textarea.scrollHeight}px`
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
    <section className="composer" aria-label="Project prompt composer">
      <div className="composer__input-wrap">
        <textarea
          aria-label="Prompt"
          className="composer__textarea"
          onChange={handleChange}
          placeholder="Do anything"
          ref={textareaRef}
          rows={2}
          value={prompt}
        />
      </div>

      <div className="composer__toolbar">
        <div className="composer__group">
          <button className="round-button" type="button" aria-label="Add attachment">
            <MaterialIcon name="add" />
          </button>

          <button className="pill-button" type="button">
            <MaterialIcon name="back_hand" />
            <span>Default permissions</span>
            <MaterialIcon name="keyboard_arrow_down" />
          </button>

          <button className="pill-button" type="button">
            <strong>5.5</strong>
            <span>High</span>
            <MaterialIcon name="keyboard_arrow_down" />
          </button>

          <button className="pill-button pill-button--agents" type="button">
            <span className="agent-stack" aria-hidden="true">
              <span>
                <MaterialIcon name="smart_toy" />
              </span>
              <span>
                <MaterialIcon name="psychology" />
              </span>
            </span>
            <span className="agent-count">+2</span>
            <MaterialIcon name="keyboard_arrow_down" />
          </button>
        </div>

        <div className="composer__group">
          <button className="round-button" type="button" aria-label="Use microphone">
            <MaterialIcon name="mic" />
          </button>
          <button
            className="round-button round-button--disabled"
            disabled={!prompt.trim()}
            type="button"
            aria-label="Send prompt"
          >
            <MaterialIcon name="arrow_upward" />
          </button>
        </div>
      </div>

      <div className="composer__context">
        <label className="context-chip context-chip--select">
          <MaterialIcon name="folder" />
          <select
            aria-label="Select project"
            className="context-chip__select"
            onChange={(event) => setSelectedProjectId(event.target.value)}
            value={selectedProjectId}
          >
            {projects.length > 0 ? (
              projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))
            ) : (
              <option value="">No projects</option>
            )}
          </select>
          <MaterialIcon name="expand_more" />
        </label>

        {contextItems.map((item) => (
          <button className="context-chip" type="button" key={item.label}>
            <MaterialIcon name={item.icon} />
            <span>{item.label}</span>
            <MaterialIcon name="expand_more" />
          </button>
        ))}
      </div>
    </section>
  )
}

export default PromptComposer
