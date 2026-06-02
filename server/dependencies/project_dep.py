from db.database import database

from db.project import ProjectRepository

from db.project_agent import ProjectAgentRepository

from services.project_service import ProjectService

project_repository = ProjectRepository(
    database
)

project_agent_repository = ProjectAgentRepository(
    database
)

project_service = ProjectService(
    database,
    project_repository,
    project_agent_repository
)