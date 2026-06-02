import streamlit as st
import requests
import json
from typing import List

# Constants
API_URL = "http://localhost:8000"

# Function to get all tasks
def get_tasks():
    response = requests.get(f"{API_URL}/tasks")
    if response.status_code == 200:
        return response.json()
    else:
        return []

# Function to create a task
def create_task(title, description, status):
    task = {"title": title, "description": description, "status": status}
    response = requests.post(f"{API_URL}/tasks", json=task)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Function to get a task by id
def get_task(id):
    response = requests.get(f"{API_URL}/tasks/{id}")
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Function to update a task
def update_task(id, title, description, status):
    task = {"title": title, "description": description, "status": status}
    response = requests.put(f"{API_URL}/tasks/{id}", json=task)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Function to delete a task
def delete_task(id):
    response = requests.delete(f"{API_URL}/tasks/{id}")
    if response.status_code == 200:
        return True
    else:
        return False

# Streamlit app
def main():
    st.title("Task Management App")
    st.session_state.tasks = get_tasks()

    # Task list view
    st.header("Task List")
    status_filter = st.selectbox("Status Filter", ["All", "todo", "in-progress", "done"])
    if status_filter == "All":
        tasks_to_show = st.session_state.tasks
    else:
        tasks_to_show = [task for task in st.session_state.tasks if task["status"] == status_filter]

    for i, task in enumerate(tasks_to_show):
        st.write(f"Task {i+1}: {task['title']}")
        st.write(f"Description: {task['description']}")
        st.write(f"Status: {task['status']}")
        st.write(f"ID: {task['id']}")
        st.write("")

    # Task form
    st.header("Create Task")
    with st.form("create_task"):
        title = st.text_input("Title")
        description = st.text_input("Description")
        status = st.selectbox("Status", ["todo", "in-progress", "done"])
        submitted = st.form_submit_button("Create Task")
        if submitted:
            new_task = create_task(title, description, status)
            if new_task:
                st.session_state.tasks.append(new_task)
                st.success("Task created successfully")
            else:
                st.error("Failed to create task")

    # CRUD buttons
    st.header("CRUD Operations")
    task_id = st.number_input("Task ID", min_value=0, step=1)
    if st.button("Get Task"):
        task = get_task(task_id)
        if task:
            st.write(f"Task {task_id}: {task['title']}")
            st.write(f"Description: {task['description']}")
            st.write(f"Status: {task['status']}")
        else:
            st.error("Task not found")

    with st.form("update_task"):
        title = st.text_input("Title")
        description = st.text_input("Description")
        status = st.selectbox("Status", ["todo", "in-progress", "done"])
        submitted = st.form_submit_button("Update Task")
        if submitted:
            updated_task = update_task(task_id, title, description, status)
            if updated_task:
                for i, task in enumerate(st.session_state.tasks):
                    if task["id"] == task_id:
                        st.session_state.tasks[i] = updated_task
                        st.success("Task updated successfully")
                        break
            else:
                st.error("Failed to update task")

    if st.button("Delete Task"):
        if delete_task(task_id):
            st.session_state.tasks = [task for task in st.session_state.tasks if task["id"] != task_id]
            st.success("Task deleted successfully")
        else:
            st.error("Failed to delete task")

if __name__ == "__main__":
    main()