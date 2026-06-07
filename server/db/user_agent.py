from db.database import Database


class UserAgentRepository:
    def __init__(self, db: Database):
        self.db = db

    async def download_agent(self, conn, user_id: str, agent_id: str):
        query = """
        INSERT INTO user_agents (
            user_id,
            agent_id
        )
        VALUES (
            $1,
            $2
        )
        ON CONFLICT (user_id, agent_id) DO NOTHING
        """

        await conn.execute(query, user_id, agent_id)

    async def uninstall_agent(self, conn, user_id: str, agent_id: str):
        query = """
        DELETE FROM user_agents
        WHERE user_id = $1
          AND agent_id = $2
        """

        await conn.execute(query, user_id, agent_id)

    async def get_downloaded_agent_ids(self, conn, user_id: str) -> set[str]:
        query = """
        SELECT agent_id
        FROM user_agents
        WHERE user_id = $1
        """

        rows = await conn.fetch(query, user_id)
        return {str(row["agent_id"]) for row in rows}
