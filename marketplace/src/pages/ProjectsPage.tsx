import Icon from '../components/Icon'
import ProjectCard from '../components/projects/ProjectCard'
import { projects } from '../data/marketplace'

function ProjectsPage() {
  return (
    <section className="projects-page">
      <div className="projects-hero">
        <div>
          <span className="page-kicker">Projects</span>
          <h1>Agent-built workspaces</h1>
          <p>
            Track demo builds, the stack behind each project, and the specialist
            agents that contributed to the implementation.
          </p>
        </div>
        <div className="project-summary-grid" aria-label="Project summary">
          <div>
            <strong>3</strong>
            <span>Active projects</span>
          </div>
          <div>
            <strong>8</strong>
            <span>Agents involved</span>
          </div>
          <div>
            <strong>24h</strong>
            <span>Freshest sync</span>
          </div>
        </div>
      </div>

      <div className="projects-toolbar">
        <div className="section-heading">
          <h2>Recent Projects</h2>
        </div>
        <button type="button">
          <Icon icon="lucide:plus" />
          New Project
        </button>
      </div>

      <div className="projects-grid">
        {projects.map((project) => (
          <ProjectCard project={project} key={project.id} />
        ))}
      </div>
    </section>
  )
}

export default ProjectsPage
