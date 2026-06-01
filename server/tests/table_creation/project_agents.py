import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    os.getenv("DATABASE_URL"),
    sslmode="require"
)

cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS project_agents (
    project_id UUID NOT NULL,
    agent_id UUID NOT NULL,

    PRIMARY KEY (project_id, agent_id),

    CONSTRAINT fk_project_agents_project
        FOREIGN KEY(project_id)
        REFERENCES projects(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_project_agents_agent
        FOREIGN KEY(agent_id)
        REFERENCES agents(id)
        ON DELETE CASCADE
);
""")

conn.commit()

cur.close()
conn.close()

print("project_agents table created successfully.")