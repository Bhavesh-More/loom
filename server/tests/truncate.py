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
TRUNCATE TABLE
    user_agents,
    project_agents,
    projects,
    agent_sources,
    agents,
    users
CASCADE;
""")

conn.commit()

cur.close()
conn.close()

print("All tables truncated successfully.")
