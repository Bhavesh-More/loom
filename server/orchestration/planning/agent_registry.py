from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, StrictStr


class AgentProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: StrictStr = Field(description="The unique identifier of the agent")
    name: StrictStr = Field(description="The display name of the agent")
    category: Literal["database", "backend", "frontend", "infrastructure", "general"] = Field(
        description="The operational category of the agent"
    )
    description: StrictStr = Field(description="A descriptive summary of what the agent does")
    capabilities: list[StrictStr] = Field(
        default_factory=list,
        description="A list of technical skills and capabilities of the agent"
    )
    model_profile: StrictStr = Field(
        description="The LLM model profile used by the agent"
    )
    cost_category: Literal["low", "medium", "high"] = Field(
        description="The relative cost category of running this agent"
    )


# Registry of all supported agents and their metadata
AGENT_REGISTRY: dict[str, AgentProfile] = {
    "postgresql": AgentProfile(
        id="postgresql",
        name="PostgreSQL Database Agent",
        category="database",
        description="Handles PostgreSQL database interactions, schema design, queries, migrations, and optimization.",
        capabilities=["sql", "postgresql", "schema_design", "migrations", "indexing", "queries", "ddl", "dml"],
        model_profile="qwen/qwen3-32b",
        cost_category="medium",
    ),
    "mongodb": AgentProfile(
        id="mongodb",
        name="MongoDB Database Agent",
        category="database",
        description="Handles MongoDB document database operations, schema-less design, aggregation pipelines, and indexing.",
        capabilities=["nosql", "mongodb", "documents", "aggregation", "collections", "indexing", "queries"],
        model_profile="qwen/qwen3-32b",
        cost_category="medium",
    ),
    "supabase": AgentProfile(
        id="supabase",
        name="Supabase Agent",
        category="database",
        description="Handles Supabase integration, including database management, Realtime subscriptions, Edge Functions, and storage.",
        capabilities=["supabase", "postgres", "realtime", "edge_functions", "row_level_security", "storage"],
        model_profile="qwen/qwen3-32b",
        cost_category="medium",
    ),
    "redis": AgentProfile(
        id="redis",
        name="Redis Cache Agent",
        category="database",
        description="Handles Redis caching, key-value storage, Pub/Sub channels, session management, and rate limiting.",
        capabilities=["redis", "caching", "key_value", "pub_sub", "session_management", "rate_limiting", "data_structures"],
        model_profile="qwen/qwen3-32b",
        cost_category="low",
    ),
    "fastapi": AgentProfile(
        id="fastapi",
        name="FastAPI Backend Agent",
        category="backend",
        description="Builds high-performance REST APIs using FastAPI, including route definition, dependency injection, and Pydantic integration.",
        capabilities=["fastapi", "python", "rest_api", "routing", "dependencies", "pydantic", "request_response", "asyncio"],
        model_profile="qwen/qwen3-32b",
        cost_category="medium",
    ),
    "auth": AgentProfile(
        id="auth",
        name="Authentication Agent",
        category="backend",
        description="Implements authentication and authorization systems, including JWT, OAuth2, session management, and password hashing.",
        capabilities=["authentication", "authorization", "jwt", "oauth2", "hashing", "encryption", "sessions", "security"],
        model_profile="qwen/qwen3-32b",
        cost_category="high",
    ),
    "rag": AgentProfile(
        id="rag",
        name="RAG Agent",
        category="backend",
        description="Implements Retrieval-Augmented Generation systems, vector search, embeddings, document ingestion, and chunking strategies.",
        capabilities=["rag", "vector_search", "embeddings", "vector_databases", "document_chunking", "semantic_search"],
        model_profile="qwen/qwen3-32b",
        cost_category="high",
    ),
    "openai": AgentProfile(
        id="openai",
        name="OpenAI Integration Agent",
        category="backend",
        description="Integrates OpenAI APIs, including GPT model prompt engineering, function calling, chat completion, and token management.",
        capabilities=["openai", "llm_integration", "prompt_engineering", "function_calling", "embeddings", "chat_completion"],
        model_profile="qwen/qwen3-32b",
        cost_category="high",
    ),
    "web_scraping": AgentProfile(
        id="web_scraping",
        name="Web Scraping Agent",
        category="backend",
        description="Scrapes web content using libraries like BeautifulSoup, Playwright, Scrapy, and handles dynamic content.",
        capabilities=["web_scraping", "beautifulsoup", "playwright", "scrapy", "html_parsing", "request_handling", "dynamic_content"],
        model_profile="qwen/qwen3-32b",
        cost_category="medium",
    ),
    "langgraph": AgentProfile(
        id="langgraph",
        name="LangGraph Orchestration Agent",
        category="backend",
        description="Builds stateful multi-agent workflows and graph-based agent orchestration systems using LangGraph.",
        capabilities=["langgraph", "state_management", "agent_workflows", "graph_orchestration", "nodes_edges"],
        model_profile="qwen/qwen3-32b",
        cost_category="high",
    ),
    "streamlit": AgentProfile(
        id="streamlit",
        name="Streamlit Frontend Agent",
        category="frontend",
        description="Builds interactive web interfaces and data dashboards using Streamlit, using state management and custom components.",
        capabilities=["streamlit", "python", "frontend", "ui_widgets", "dashboards", "state_management", "data_visualization"],
        model_profile="qwen/qwen3-32b",
        cost_category="low",
    ),
    "pytest": AgentProfile(
        id="pytest",
        name="Pytest Testing Agent",
        category="infrastructure",
        description="Designs and runs automated tests using Pytest, including fixtures, mocking, parameterized tests, and assertions.",
        capabilities=["pytest", "unit_testing", "fixtures", "mocking", "parameterized_testing", "code_coverage", "assertions"],
        model_profile="qwen/qwen3-32b",
        cost_category="low",
    ),
    "docker": AgentProfile(
        id="docker",
        name="Docker Containerization Agent",
        category="infrastructure",
        description="Creates and manages Docker containers, custom Dockerfiles, multi-stage builds, and docker-compose configurations.",
        capabilities=["docker", "dockerfile", "docker_compose", "containerization", "networking", "volumes", "multi_stage_builds"],
        model_profile="qwen/qwen3-32b",
        cost_category="medium",
    ),
    "github_actions": AgentProfile(
        id="github_actions",
        name="GitHub Actions Agent",
        category="infrastructure",
        description="Sets up CI/CD pipelines, workflows, triggers, actions, secrets, and environment configurations in GitHub Actions.",
        capabilities=["github_actions", "ci_cd", "workflows", "yaml", "runners", "secrets_management"],
        model_profile="qwen/qwen3-32b",
        cost_category="medium",
    ),
    "all_rounder": AgentProfile(
        id="all_rounder",
        name="All Rounder Agent",
        category="general",
        description="A versatile agent capable of handling general programming tasks, writing READMEs, scripting, refactoring, and orchestrating other components.",
        capabilities=["python", "general_programming", "readme", "markdown", "refactoring", "scripting", "debugging", "glue_code"],
        model_profile="qwen/qwen3-32b",
        cost_category="high",
    ),
}


def get_agent_profile(agent_id: str) -> AgentProfile | None:
    """Retrieve the capability profile of an agent by its ID."""
    return AGENT_REGISTRY.get(agent_id)


def list_agent_profiles() -> list[AgentProfile]:
    """Retrieve all registered agent profiles."""
    return list(AGENT_REGISTRY.values())
