from fastapi import APIRouter

from db.database import database

router = APIRouter(
    prefix="/agents",
    tags=["Agents"]
)

AGENT_METADATA = {
    "204cfaf9-aa29-430f-9309-4a97e81e7791": {
        "rating": "4.8",
        "icon": "speed",
        "tone": "amber",
        "synced": "Synced 2h ago",
        "installs": "12.4k",
    },
    "ee1b6b17-a05d-4e4f-a313-cdae446f62c0": {
        "rating": "4.7",
        "icon": "dashboard",
        "tone": "green",
        "synced": "Synced 1h ago",
        "installs": "9.8k",
    },
    "fdcc23b6-0106-459e-8b0e-29072d34b28c": {
        "rating": "4.9",
        "icon": "database",
        "tone": "blue",
        "synced": "Synced 3h ago",
        "installs": "15.2k",
    },
    "ef209bcf-caca-43d8-9d4d-33c47af59141": {
        "rating": "4.8",
        "icon": "storage",
        "tone": "violet",
        "synced": "Synced 2h ago",
        "installs": "11.5k",
    },
    "7f52aad5-5292-436e-a7a7-e7056f0361bd": {
        "rating": "4.6",
        "icon": "memory",
        "tone": "sky",
        "synced": "Synced 4h ago",
        "installs": "7.3k",
    },
    "8ac481f3-a4e9-4d95-b065-4726e7c1d0f8": {
        "rating": "4.7",
        "icon": "lock",
        "tone": "green",
        "synced": "Synced 5h ago",
        "installs": "3.2k",
    },
    "ea173cc5-68ce-4711-9428-a09039e61e41": {
        "rating": "4.6",
        "icon": "account_tree",
        "tone": "blue",
        "synced": "Synced 6h ago",
        "installs": "2.1k",
    },
    "4c38ec8e-b2b0-42c1-a78b-ded28fd14138": {
        "rating": "4.9",
        "icon": "smart_toy",
        "tone": "rose",
        "synced": "Synced 8h ago",
        "installs": "5.6k",
    },
    "9d4bd9f2-263e-4f88-80c0-a83cd556f9de": {
        "rating": "4.5",
        "icon": "package",
        "tone": "sky",
        "synced": "Synced 3h ago",
        "installs": "8.4k",
    },
    "00ac1046-fc5b-4c9b-a7a3-15f94545b1a2": {
        "rating": "4.6",
        "icon": "terminal",
        "tone": "green",
        "synced": "Synced 4h ago",
        "installs": "6.1k",
    },
    "4cb0bc25-7486-4fc8-823b-cb2475f0fdd5": {
        "rating": "4.8",
        "icon": "verified_user",
        "tone": "amber",
        "synced": "Synced 2h ago",
        "installs": "13.7k",
    },
    "99fb18b4-39b7-4b9f-848f-ec8c8e1c17b0": {
        "rating": "4.7",
        "icon": "psychology",
        "tone": "violet",
        "synced": "Synced 5h ago",
        "installs": "10.2k",
    },
    "fb64a956-f8af-43f9-b6c8-c3b46626ee8a": {
        "rating": "4.4",
        "icon": "science",
        "tone": "rose",
        "synced": "Synced 7h ago",
        "installs": "5.6k",
    },
    "1f4ddc23-02c6-4e4a-8ca9-4b09bb37f198": {
        "rating": "4.5",
        "icon": "travel_explore",
        "tone": "blue",
        "synced": "Synced 8h ago",
        "installs": "4.9k",
    },
}

@router.get("")
async def get_agents():
    conn = await database.get_conn()
    try:
        agent_rows = await conn.fetch("SELECT * FROM agents")
        source_rows = await conn.fetch("SELECT agent_id, url FROM agent_sources WHERE is_active = TRUE")
        
        sources_by_agent = {}
        for s in source_rows:
            agent_id_str = str(s["agent_id"])
            if agent_id_str not in sources_by_agent:
                sources_by_agent[agent_id_str] = []
            sources_by_agent[agent_id_str].append(s["url"])
            
        agents = []
        for row in agent_rows:
            agent_dict = dict(row)
            agent_id_str = str(agent_dict["id"])
            
            agent_type = "Core" if agent_dict.get("is_core", True) else "Community"
            
            version = agent_dict.get("version", "1.0.0")
            if version and not version.startswith("v"):
                version = f"v{version}"
                
            metadata = AGENT_METADATA.get(agent_id_str, {
                "rating": "4.5",
                "icon": "smart_toy",
                "tone": "blue",
                "synced": "Synced just now",
                "installs": "0",
            })
            
            agents.append({
                "id": agent_id_str,
                "name": agent_dict["name"],
                "version": version,
                "type": agent_type,
                "description": agent_dict.get("description") or "",
                "sources": sources_by_agent.get(agent_id_str, []),
                "rating": metadata["rating"],
                "icon": metadata["icon"],
                "tone": metadata["tone"],
                "synced": metadata["synced"],
                "installs": metadata["installs"]
            })
            
        return agents
    finally:
        await database.release_conn(conn)
