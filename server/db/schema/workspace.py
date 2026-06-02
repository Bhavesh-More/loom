from pydantic import BaseModel
from typing import List, Optional

class FileTreeNode(BaseModel):
    name: str
    path: str
    type: str  # "file" or "directory"
    children: Optional[List["FileTreeNode"]] = None

class FileContentResponse(BaseModel):
    path: str
    content: str

class SaveFileRequest(BaseModel):
    path: str
    content: str
