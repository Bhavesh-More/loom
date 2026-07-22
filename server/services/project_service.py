from pathlib import Path


class ProjectService:
    def __init__(
        self,
        db,
        project_repository,
        project_agent_repository
    ):
        self.db = db
        self.project_repository = project_repository
        self.project_agent_repository = project_agent_repository


    async def create_project(
        self,
        user_id: str,
        name: str,
        description: str | None,
        agent_ids: list[str]
    ):
        conn = await self.db.get_conn()

        try:

            async with conn.transaction():

                project = await self.project_repository.create_project(
                    conn=conn,
                    user_id=user_id,
                    name=name,
                    description=description
                )

                await self.project_agent_repository.add_agents(
                    conn=conn,
                    project_id=str(project["id"]),
                    agent_ids=[str(agent_id) for agent_id in agent_ids]
                )

            await self._create_workspace(
                str(project["id"])
            )

            return {
                "project_id": project["id"],
                "name": project["name"],
                "description": project["description"],
                "status": project["status"]
            }

        finally:
            await self.db.release_conn(conn)


    async def get_project(
        self,
        project_id: str,
        user_id: str
    ):
        conn = await self.db.get_conn()

        try:
            return await self.project_repository.get_project_by_id_for_user(
                conn=conn,
                project_id=project_id,
                user_id=user_id
            )
        finally:
            await self.db.release_conn(conn)


    async def get_projects(self, user_id: str):
        conn = await self.db.get_conn()

        try:
            return await self.project_repository.get_projects(
                conn=conn,
                user_id=user_id
            )
        finally:
            await self.db.release_conn(conn)


    async def _create_workspace(
        self,
        project_id: str
    ):
        root = Path("workspaces") / project_id

        (root / "backend").mkdir(
            parents=True,
            exist_ok=True
        )

        (root / "frontend").mkdir(
            parents=True,
            exist_ok=True
        )

        (root / "docs").mkdir(
            parents=True,
            exist_ok=True
        )
