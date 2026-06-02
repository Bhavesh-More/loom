from .base_repository import BaseRepository


class ProjectAgentRepository(BaseRepository):

    async def add_agents(
        self,
        conn,
        project_id: str,
        agent_ids: list[str]
    ):
        query = """
        INSERT INTO project_agents (
            project_id,
            agent_id
        )
        VALUES (
            $1,
            $2
        )
        """

        await conn.executemany(
            query,
            [
                (project_id, agent_id)
                for agent_id in agent_ids
            ]
        )

    async def get_project_agents(
        self,
        conn,
        project_id: str
    ):
        query = """
        SELECT agent_id
        FROM project_agents
        WHERE project_id = $1
        """

        rows = await conn.fetch(
            query,
            project_id
        )

        return [str(row["agent_id"]) for row in rows]