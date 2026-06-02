# Database Schema

---

## users

Stores user accounts.

| Column | Type | Constraints |
|----------|----------|----------|
| id | UUID | PK |
| email | TEXT | UNIQUE, NOT NULL |
| name | TEXT | NOT NULL |
| created_at | TIMESTAMP | DEFAULT NOW() |

### Relationships

- One user can create many agents.
- One user can own many projects.

---

## agents

Stores AI agents available in the marketplace.

| Column | Type | Constraints |
|----------|----------|----------|
| id | UUID | PK |
| name | TEXT | NOT NULL |
| description | TEXT | NULL |
| created_by | UUID | FK → users.id |
| is_core | BOOLEAN | DEFAULT FALSE |
| is_public | BOOLEAN | DEFAULT FALSE |
| version | TEXT | DEFAULT '1.0.0' |
| last_kb_update | TIMESTAMP | NULL |
| created_at | TIMESTAMP | DEFAULT NOW() |
| updated_at | TIMESTAMP | DEFAULT NOW() |

### Relationships

- Many agents can belong to one user.
- One agent can have many sources.
- One agent can be attached to many projects.

### Examples

- FastAPI Agent
- MongoDB Agent
- Redis Agent
- React Agent
- Documentation Agent

---

## agent_sources

Stores knowledge sources attached to agents.

| Column | Type | Constraints |
|----------|----------|----------|
| id | UUID | PK |
| agent_id | UUID | FK → agents.id |
| url | TEXT | NOT NULL |
| source_type | TEXT | NOT NULL |
| is_active | BOOLEAN | DEFAULT TRUE |
| last_scraped_at | TIMESTAMP | NULL |

### Relationships

- Many sources belong to one agent.

### Example Source Types

- website
- github
- docs
- pdf
- youtube

### Example URLs

- https://fastapi.tiangolo.com
- https://redis.io/docs
- https://github.com/langchain-ai/langgraph

---

## projects

Stores user-created projects.

| Column | Type | Constraints |
|----------|----------|----------|
| id | UUID | PK |
| user_id | UUID | FK → users.id |
| name | TEXT | NOT NULL |
| description | TEXT | NULL |
| status | TEXT | DEFAULT 'active' |
| created_at | TIMESTAMP | DEFAULT NOW() |
| updated_at | TIMESTAMP | DEFAULT NOW() |

### Relationships

- Many projects belong to one user.
- One project can contain many agents.

### Example Status Values

- active
- completed
- archived

---

## project_agents

Join table connecting projects and agents.

| Column | Type | Constraints |
|----------|----------|----------|
| project_id | UUID | PK, FK → projects.id |
| agent_id | UUID | PK, FK → agents.id |

### Relationships

- Many-to-many between projects and agents.

### Example

Project:
- "Build SaaS Analytics Platform"

Assigned Agents:
- FastAPI Agent
- PostgreSQL Agent
- React Agent
- Docker Agent

---

# ER Diagram

users
│
├── agents
│      └── agent_sources
│
└── projects
       │
       └── project_agents
               │
               └── agents