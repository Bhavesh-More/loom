from uuid import UUID


class ProjectDB:
    def __init__(self, db):
        self.db = db


    def create_project(
        self,
        conn,
        user_id: UUID,
        name: str,
        description: str | None,
    ):
        query = """
        INSERT INTO projects (
            user_id,
            name,
            description
        )
        VALUES (%s, %s, %s)
        RETURNING id, user_id, name, description, status, created_at;
        """

        with conn.cursor() as cur:
            cur.execute(
                query,
                (
                    str(user_id),
                    name,
                    description,
                ),
            )

            row = cur.fetchone()

        return {
            "id": row[0],
            "user_id": row[1],
            "name": row[2],
            "description": row[3],
            "status": row[4],
            "created_at": row[5],
        }


    def get_project_by_id(self, conn, project_id: UUID):
        query = """
        SELECT
            id,
            user_id,
            name,
            description,
            status,
            created_at,
            updated_at
        FROM projects
        WHERE id = %s
        """

        with conn.cursor() as cur:
            cur.execute(query, (str(project_id),))
            row = cur.fetchone()

        if not row:
            return None

        return {
            "id": row[0],
            "user_id": row[1],
            "name": row[2],
            "description": row[3],
            "status": row[4],
            "created_at": row[5],
            "updated_at": row[6],
        }