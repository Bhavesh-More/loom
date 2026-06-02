import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DEV_USER_ID = "11111111-1111-1111-1111-111111111111"

conn = psycopg2.connect(
    os.getenv("DATABASE_URL"),
    sslmode="require"
)

cur = conn.cursor()

cur.execute("""
INSERT INTO users (
    id,
    email,
    name
)
VALUES (
    %s,
    %s,
    %s
)
ON CONFLICT (id) DO NOTHING;
""", (
    DEV_USER_ID,
    "dev@example.com",
    "Dev User"
))

conn.commit()

cur.close()
conn.close()

print("Dev user created.")