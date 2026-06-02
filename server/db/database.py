from psycopg2.pool import SimpleConnectionPool
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.pool = SimpleConnectionPool(
            minconn=5,
            maxconn=20,
            dsn=os.getenv("DATABASE_URL")
        )

    def get_conn(self):
        return self.pool.getconn()

    def release_conn(self, conn):
        self.pool.putconn(conn)