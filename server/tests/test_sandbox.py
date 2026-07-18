import pytest
import time
import os
from sandbox.manager import SandboxManager
from sandbox import config
from sandbox import fs_tools
from sandbox import manifest

@pytest.fixture(scope="module")
def mgr():
    # Make sure base image is built or available before running tests
    # For now assume it is built.
    manager = SandboxManager()
    yield manager
    
    # Clean up any test projects
    manager.destroy("test_proj_1")
    manager.destroy("test_proj_2")

def test_get_or_create_idempotent(mgr):
    project_id = "test_proj_1"
    
    # Clean state
    mgr.destroy(project_id)
    
    c1 = mgr.get_or_create(project_id)
    assert c1.status == "created" or c1.status == "running"
    
    # Must reuse
    c2 = mgr.get_or_create(project_id)
    assert c1.id == c2.id
    
    mgr.destroy(project_id)

def test_write_and_read_file(mgr):
    project_id = "test_proj_1"
    mgr.destroy(project_id)
    mgr.get_or_create(project_id)
    
    # Should not exist
    with pytest.raises(RuntimeError):
        fs_tools.list_files(project_id, "nonexistent")

    # Create file
    content = "hello world"
    fs_tools.write_new_file(project_id, "test.txt", content)
    
    # Read file
    read_back = fs_tools.read_file(project_id, "test.txt")
    assert read_back.strip() == content
    
    # List files
    files = fs_tools.list_files(project_id)
    assert "./test.txt" in files
    
    mgr.destroy(project_id)

def test_edit_file(mgr):
    project_id = "test_proj_1"
    mgr.destroy(project_id)
    
    fs_tools.write_new_file(project_id, "test_edit.py", "def foo():\n    return 1\n")
    
    # Success case
    fs_tools.edit_file(project_id, "test_edit.py", "return 1", "return 2")
    content = fs_tools.read_file(project_id, "test_edit.py")
    assert "return 2" in content
    
    # Fail case - not found
    with pytest.raises(ValueError, match="not found"):
        fs_tools.edit_file(project_id, "test_edit.py", "return 3", "return 4")
        
    # Fail case - multiple
    fs_tools.write_new_file(project_id, "test_multi.py", "A\nA\nA\n")
    with pytest.raises(ValueError, match="not unique"):
        fs_tools.edit_file(project_id, "test_multi.py", "A", "B")
        
    mgr.destroy(project_id)

def test_persistence_across_stops(mgr):
    project_id = "test_proj_1"
    mgr.destroy(project_id)
    
    fs_tools.write_new_file(project_id, "persist.txt", "keep me")
    mgr.stop(project_id)
    
    # get_or_create should restart
    mgr.get_or_create(project_id)
    content = fs_tools.read_file(project_id, "persist.txt")
    assert content.strip() == "keep me"
    
    mgr.destroy(project_id)

def test_manifest(mgr):
    project_id = "test_proj_2"
    mgr.destroy(project_id)
    
    m = manifest.load_manifest(project_id)
    assert m == {"files": {}, "conventions": []}
    
    manifest.register_file(project_id, "app.py", "Main app entrypoint")
    m2 = manifest.load_manifest(project_id)
    assert "app.py" in m2["files"]
    assert m2["files"]["app.py"] == "Main app entrypoint"
    
    mgr.destroy(project_id)

def test_run_command(mgr):
    project_id = "test_proj_1"
    mgr.destroy(project_id)
    
    res = fs_tools.run_command(project_id, ["echo", "hello sandbox"])
    assert res["exit_code"] == 0
    assert "hello sandbox" in res["stdout"]
    
    mgr.destroy(project_id)

def test_command_timeout(mgr):
    project_id = "test_proj_1"
    mgr.destroy(project_id)
    
    # We rely on the `timeout` wrapper implemented in manager.exec_run
    # Let's run a sleep that exceeds a short timeout
    res = mgr.exec_run(project_id, ["sleep", "10"], timeout=1)
    
    # timeout command usually returns 124 or 137 if killed
    assert res["exit_code"] != 0
    
    mgr.destroy(project_id)
