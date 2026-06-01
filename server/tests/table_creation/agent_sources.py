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
CREATE TABLE IF NOT EXISTS agent_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL,
    url TEXT NOT NULL,
    source_type TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    last_scraped_at TIMESTAMP,
    
    CONSTRAINT fk_agent_sources_agent
        FOREIGN KEY(agent_id)
        REFERENCES agents(id)
        ON DELETE CASCADE
);
""")

conn.commit()

cur.close()
conn.close()

print("agent_sources table created successfully.")