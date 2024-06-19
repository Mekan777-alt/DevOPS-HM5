from pydantic import BaseModel
from typing import Optional, Dict


class Task(BaseModel):
    taskID: Optional[str] = None
    name: str
    description: str
    params: Optional[Dict[str, str]] = None
