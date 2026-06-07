import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    os.getenv("DATABASE_URL"),
    sslmode="require"
)

cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS user_agents (
    user_id UUID NOT NULL,
    agent_id UUID NOT NULL,
    downloaded_at TIMESTAMP DEFAULT NOW(),

    PRIMARY KEY (user_id, agent_id),

    CONSTRAINT fk_user_agents_user
        FOREIGN KEY(user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_user_agents_agent
        FOREIGN KEY(agent_id)
        REFERENCES agents(id)
        ON DELETE CASCADE
);
""")

conn.commit()

cur.close()
conn.close()

print("user_agents table created successfully.")
