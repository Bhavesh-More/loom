import os
import random
from datetime import datetime, timedelta

import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    os.getenv("DATABASE_URL"),
    sslmode="require"
)

cur = conn.cursor()

# Fetch all agents
cur.execute("""
SELECT id, name
FROM agents;
""")

agent_map = {
    name: agent_id
    for agent_id, name in cur.fetchall()
}

agent_sources = {
    "FastAPI Agent": [
        "https://fastapi.tiangolo.com/",
        "https://docs.pydantic.dev/"
    ],
    "Streamlit Agent": [
        "https://docs.streamlit.io/",
        "https://streamlit.io/"
    ],
    "MongoDB Agent": [
        "https://www.mongodb.com/docs/",
        "https://www.mongodb.com/atlas/database"
    ],
    "PostgreSQL Agent": [
        "https://www.postgresql.org/docs/",
        "https://www.postgresql.org/"
    ],
    "Redis Agent": [
        "https://redis.io/docs/latest/",
        "https://redis.io/"
    ],
    "Supabase Agent": [
        "https://supabase.com/docs",
        "https://supabase.com/"
    ],
    "LangGraph Agent": [
        "https://langchain-ai.github.io/langgraph/",
        "https://python.langchain.com/"
    ],
    "OpenAI Agent": [
        "https://platform.openai.com/docs",
        "https://openai.com/"
    ],
    "Docker Agent": [
        "https://docs.docker.com/",
        "https://www.docker.com/"
    ],
    "GitHub Actions Agent": [
        "https://docs.github.com/actions",
        "https://github.com/features/actions"
    ],
    "Authentication Agent": [
        "https://auth0.com/docs",
        "https://clerk.com/docs"
    ],
    "RAG Agent": [
        "https://python.langchain.com/docs/",
        "https://www.pinecone.io/learn/"
    ],
    "Pytest Agent": [
        "https://docs.pytest.org/",
        "https://docs.python.org/3/"
    ],
    "Web Scraping Agent": [
        "https://beautiful-soup-4.readthedocs.io/",
        "https://www.scrapy.org/"
    ]
}

for agent_name, urls in agent_sources.items():

    agent_id = agent_map.get(agent_name)

    if not agent_id:
        print(f"Skipping {agent_name} - not found")
        continue

    for url in urls:

        scraped_time = (
            datetime.now()
            - timedelta(
                days=random.randint(0, 7),
                hours=random.randint(0, 23)
            )
        )

        cur.execute(
            """
            INSERT INTO agent_sources (
                agent_id,
                url,
                source_type,
                is_active,
                last_scraped_at
            )
            VALUES (
                %s,
                %s,
                'website',
                TRUE,
                %s
            );
            """,
            (
                agent_id,
                url,
                scraped_time
            )
        )

conn.commit()

cur.close()
conn.close()

print("Agent sources inserted successfully.")