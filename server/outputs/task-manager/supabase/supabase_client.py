import os
from supabase import create_client, Client

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def get_tasks():
    data = supabase.from_("tasks").select("*")
    return data

def create_task(title: str, description: str, status: str = 'todo'):
    data = supabase.from_("tasks").insert([{"title": title, "description": description, "status": status}])
    return data

def update_task(id: int, title: str = None, description: str = None, status: str = None):
    data = supabase.from_("tasks").update([{"id": id, "title": title, "description": description, "status": status}])
    return data

def delete_task(id: int):
    data = supabase.from_("tasks").delete([{"id": id}])
    return data