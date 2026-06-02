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

agents = [
    (
        "FastAPI Agent",
        "Fast API routing, validation, and async service scaffolding."
    ),
    (
        "Streamlit Agent",
        "Rapid data apps, dashboards, and internal tools in minutes."
    ),
    (
        "MongoDB Agent",
        "Document modeling, indexes, and aggregation pipeline helpers."
    ),
    (
        "PostgreSQL Agent",
        "Schemas, joins, query tuning, and migration-friendly workflows."
    ),
    (
        "Redis Agent",
        "Caching, queues, and ultra-fast key value primitives."
    ),
    (
        "Supabase Agent",
        "Auth, database, storage, and realtime backend workflows."
    ),
    (
        "LangGraph Agent",
        "Stateful multi-step graphs for complex LLM workflows."
    ),
    (
        "OpenAI Agent",
        "Prompting, tool use, and model orchestration for app workflows."
    ),
    (
        "Docker Agent",
        "Container builds, image hygiene, and compose setups."
    ),
    (
        "GitHub Actions Agent",
        "CI pipelines, automation, and release workflow helpers."
    ),
    (
        "Authentication Agent",
        "Login flows, sessions, and secure access patterns."
    ),
    (
        "RAG Agent",
        "Retrieval, chunking, and answer-grounding workflows."
    ),
    (
        "Pytest Agent",
        "Test layout, fixtures, and clean Python test patterns."
    ),
    (
        "Web Scraping Agent",
        "Page parsing, selectors, and safe extraction workflows."
    ),
]

for name, description in agents:

    days_ago = random.randint(0, 14)

    random_timestamp = (
        datetime.now()
        - timedelta(
            days=days_ago,
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
    )

    cur.execute(
        """
        INSERT INTO agents (
            name,
            description,
            is_core,
            is_public,
            version,
            last_kb_update,
            created_at,
            updated_at
        )
        VALUES (
            %s,
            %s,
            TRUE,
            TRUE,
            '1.0.0',
            %s,
            %s,
            %s
        )
        ON CONFLICT DO NOTHING;
        """,
        (
            name,
            description,
            random_timestamp,
            random_timestamp,
            random_timestamp
        )
    )

conn.commit()

cur.close()
conn.close()

print(f"Inserted {len(agents)} demo agents.")