from .base_repository import BaseRepository


class ProjectRepository(BaseRepository):

    async def create_project(
        self,
        conn,
        user_id: str,
        name: str,
        description: str | None
    ):
        query = """
        INSERT INTO projects (
            user_id,
            name,
            description
        )
        VALUES (
            $1,
            $2,
            $3
        )
        RETURNING
            id,
            user_id,
            name,
            description,
            status,
            created_at,
            updated_at;
        """

        row = await conn.fetchrow(
            query,
            user_id,
            name,
            description
        )

        return dict(row)

    async def get_project_by_id(
        self,
        conn,
        project_id: str
    ):
        query = """
        SELECT *
        FROM projects
        WHERE id = $1
        """

        row = await conn.fetchrow(
            query,
            project_id
        )

        if not row:
            return None

        return dict(row)