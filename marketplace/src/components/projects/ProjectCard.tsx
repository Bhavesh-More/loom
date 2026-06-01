import type { Project } from '../../types/marketplace'
import Icon from '../Icon'

type ProjectCardProps = {
  project: Project
}

function ProjectCard({ project }: ProjectCardProps) {
  return (
    <article className="project-card">
      <div className="project-card-top">
        <div className="project-title-row">
          <div className={project.accentClass}>
            <Icon icon="lucide:folder-kanban" className="icon-slate" />
          </div>
          <div>
            <h3>{project.name}</h3>
            <span>{project.updated}</span>
          </div>
        </div>
        <strong className={project.statusClass}>{project.status}</strong>
      </div>

      <p className="project-description">{project.description}</p>

      <div className="project-stack">
        {project.stack.map((item) => (
          <span className="source-tag" key={`${project.id}-${item}`}>
            {item}
          </span>
        ))}
      </div>

      <div className="project-contributors">
        <p>Agents contributed</p>
        <div className="contributor-list">
          {project.contributors.map((contributor) => (
            <div className="contributor-row" key={`${project.id}-${contributor.name}`}>
              <span className="contributor-icon">
                <Icon icon={contributor.icon} className={contributor.iconClass} />
              </span>
              <div>
                <strong>{contributor.name}</strong>
                <span>{contributor.role}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </article>
  )
}

export default ProjectCard
