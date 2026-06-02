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
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
    role TEXT NOT NULL,
    message_type TEXT NOT NULL,
    content JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_chat_messages_session
        FOREIGN KEY(session_id)
        REFERENCES chat_sessions(id)
        ON DELETE CASCADE,

    CONSTRAINT chk_chat_messages_role
        CHECK (
            role IN (
                'user',
                'assistant',
                'agent',
                'system'
            )
        ),

    CONSTRAINT chk_chat_messages_type
        CHECK (
            message_type IN (
                'text',
                'agent_execution',
                'task_plan',
                'system_event'
            )
        )
);
""")

conn.commit()

cur.close()
conn.close()

print("chat_messages table created successfully.")