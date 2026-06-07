from uuid import UUID

from fastapi import APIRouter, HTTPException

from db.schema.project import CreateProjectRequest, CreateProjectResponse
from dependencies.project_dep import project_service
from db.chat import ChatRepository

router = APIRouter(
    prefix="/projects",
    tags=["Projects"]
)


@router.post("", response_model=CreateProjectResponse)
async def create_project(request: CreateProjectRequest):
    return await project_service.create_project(
        name=request.name,
        description=request.description,
        agent_ids=[str(agent_id) for agent_id in request.agent_ids]
    )


@router.get("/{project_id}")
async def get_project(project_id: UUID):
    project = await project_service.get_project(str(project_id))

    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    return project


@router.post("/get-projects")
async def get_projects():
    projects = await project_service.get_projects()
    return projects


from pydantic import BaseModel
from graph.builder import loom_graph
from db.database import database

def get_agent_key(agent_id_str: str, agent_name: str) -> str:
    # Explicit mapping by ID
    mapping = {
        "204cfaf9-aa29-430f-9309-4a97e81e7791": "fastapi",
        "ee1b6b17-a05d-4e4f-a313-cdae446f62c0": "streamlit",
        "fdcc23b6-0106-459e-8b0e-29072d34b28c": "mongodb",
        "ef209bcf-caca-43d8-9d4d-33c47af59141": "postgresql",
        "7f52aad5-5292-436e-a7a7-e7056f0361bd": "redis",
        "8ac481f3-a4e9-4d95-b065-4726e7c1d0f8": "supabase",
        "ea173cc5-68ce-4711-9428-a09039e61e41": "langgraph",
        "4c38ec8e-b2b0-42c1-a78b-ded28fd14138": "openai",
        "9d4bd9f2-263e-4f88-80c0-a83cd556f9de": "docker",
        "00ac1046-fc5b-4c9b-a7a3-15f94545b1a2": "github_actions",
        "4cb0bc25-7486-4fc8-823b-cb2475f0fdd5": "auth",
        "99fb18b4-39b7-4b9f-848f-ec8c8e1c17b0": "rag",
        "fb64a956-f8af-43f9-b6c8-c3b46626ee8a": "pytest",
        "1f4ddc23-02c6-4e4a-8ca9-4b09bb37f198": "web_scraping",
    }
    if agent_id_str in mapping:
        return mapping[agent_id_str]
    
    cleaned = agent_name.lower().replace(" agent", "").replace(" ", "_")
    if cleaned == "authentication":
        return "auth"
    return cleaned

import json
from fastapi.responses import StreamingResponse
from tools.file_tools import parse_agent_output

class DevelopProjectRequest(BaseModel):
    project_id: UUID
    prompt: str
    selected_agent_ids: list[UUID] = []

chat_repository = ChatRepository(database)

@router.post("/develop")
async def develop_project(request: DevelopProjectRequest):
    async def event_generator():
        conn = await database.get_conn()
        messages_to_insert = []
        chat_session_id = None
        try:
            # 1. Fetch project by ID
            project = await project_service.project_repository.get_project_by_id(conn, str(request.project_id))
            if not project:
                yield json.dumps({"type": "error", "message": "Project not found"}) + "\n"
                return

            # 2. Get agents selected for this run, falling back to project-linked agents
            agent_ids = [str(agent_id) for agent_id in request.selected_agent_ids]
            if not agent_ids:
                agent_ids = await project_service.project_agent_repository.get_project_agents(conn, str(request.project_id))
            if not agent_ids:
                yield json.dumps({
                    "type": "error",
                    "message": "No agents selected. Download agents from the Marketplace and select them before running."
                }) + "\n"
                return

            # 3. Get all agent names to map IDs to agent keys
            rows = await conn.fetch("SELECT id, name FROM agents")
            agent_id_to_name = {str(r["id"]): r["name"] for r in rows}

            selected_agents = []
            for aid in agent_ids:
                name = agent_id_to_name.get(aid)
                if name:
                    key = get_agent_key(aid, name)
                    selected_agents.append(key)

            if not selected_agents:
                yield json.dumps({"type": "error", "message": "Assigned agents could not be mapped to Loom execution keys."}) + "\n"
                return

            # Create a chat session in the DB
            chat_session = await chat_repository.create_chat_session(conn, str(request.project_id), request.prompt)
            chat_session_id = chat_session["id"]

            # Initialize messages buffer with user prompt and starting event
            messages_to_insert.append({
                "session_id": chat_session_id,
                "role": "user",
                "message_type": "text",
                "content": {"text": request.prompt}
            })

            messages_to_insert.append({
                "session_id": chat_session_id,
                "role": "system",
                "message_type": "system_event",
                "content": {
                    "text": "Starting developer workflow...",
                    "project_name": project["name"]
                }
            })

            # 4. Invoke the orchestrator using those agents
            initial_state = {
                "project_id": str(request.project_id),
                "project_name": project["name"],
                "goal": request.prompt,
                "selected_agents": selected_agents,
                "execution_plan": [],
                "current_step": 0,
                "agent_outputs": {},
                "workspace_path": "",
                "errors": []
            }

            yield json.dumps({
                "type": "start",
                "message": "Starting developer workflow...",
                "project_name": project["name"],
                "chat_id": str(chat_session_id),
                "chat_title": chat_session["title"]
            }) + "\n"

            plan = []
            async for event in loom_graph.astream(initial_state, stream_mode="updates"):
                node_name = list(event.keys())[0]
                state_update = event[node_name]
                errors = state_update.get("errors", [])

                if node_name == "planner":
                    plan = state_update.get("execution_plan", [])
                    messages_to_insert.append({
                        "session_id": chat_session_id,
                        "role": "system",
                        "message_type": "task_plan",
                        "content": {
                            "text": f"Generated plan with {len(plan)} steps.",
                            "plan": plan,
                            "errors": errors
                        }
                    })
                    yield json.dumps({
                        "type": "planner",
                        "message": f"Generated plan with {len(plan)} steps.",
                        "plan": plan,
                        "errors": errors
                    }) + "\n"
                elif node_name == "executor":
                    current_step = state_update.get("current_step", 1)
                    completed_step_idx = current_step - 1

                    agent_name = "Unknown"
                    task = ""
                    if 0 <= completed_step_idx < len(plan):
                        step_info = plan[completed_step_idx]
                        agent_name = step_info.get("agent", "Unknown")
                        task = step_info.get("task", "")

                    agent_raw_output = ""
                    agent_outputs_dict = state_update.get("agent_outputs", {})
                    if agent_name in agent_outputs_dict:
                        agent_raw_output = agent_outputs_dict[agent_name]
                    elif len(agent_outputs_dict) > 0:
                        agent_raw_output = list(agent_outputs_dict.values())[-1]

                    files_written = []
                    if agent_raw_output:
                        parsed_files = parse_agent_output(agent_raw_output)
                        files_written = list(parsed_files.keys())

                    messages_to_insert.append({
                        "session_id": chat_session_id,
                        "role": "system",
                        "message_type": "agent_execution",
                        "content": {
                            "text": f"Step {current_step} completed.",
                            "completed_step_idx": completed_step_idx,
                            "agent": agent_name,
                            "task": task,
                            "files": files_written,
                            "errors": errors
                        }
                    })
                    yield json.dumps({
                        "type": "executor",
                        "message": f"Step {current_step} completed.",
                        "completed_step_idx": completed_step_idx,
                        "agent": agent_name,
                        "task": task,
                        "files": files_written,
                        "errors": errors
                    }) + "\n"
                elif node_name == "file_writer":
                    workspace_path = state_update.get("workspace_path", "")
                    messages_to_insert.append({
                        "session_id": chat_session_id,
                        "role": "system",
                        "message_type": "system_event",
                        "content": {
                            "text": "Writing outputs to disk.",
                            "workspace_path": workspace_path,
                            "errors": errors
                        }
                    })
                    yield json.dumps({
                        "type": "file_writer",
                        "message": "Writing outputs to disk.",
                        "workspace_path": workspace_path,
                        "errors": errors
                    }) + "\n"

            messages_to_insert.append({
                "session_id": chat_session_id,
                "role": "system",
                "message_type": "system_event",
                "content": {
                    "text": "Development complete."
                }
            })
            yield json.dumps({"type": "complete", "message": "Development complete."}) + "\n"

        except Exception as e:
            if chat_session_id:
                messages_to_insert.append({
                    "session_id": chat_session_id,
                    "role": "system",
                    "message_type": "system_event",
                    "content": {
                        "text": f"LangGraph execution failed: {str(e)}"
                    }
                })
            yield json.dumps({"type": "error", "message": f"LangGraph execution failed: {str(e)}"}) + "\n"
        finally:
            if chat_session_id and messages_to_insert:
                try:
                    await chat_repository.create_chat_messages(conn, messages_to_insert)
                except Exception as db_err:
                    print(f"Failed to log chat messages: {db_err}")
            await database.release_conn(conn)

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")
