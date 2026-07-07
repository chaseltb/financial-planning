from pydantic import BaseModel
from typing import Dict, Any

class ScenarioModel(BaseModel):
    name: str
    description: str = ""
    changes: Dict[str, Any] = {}  # E.g. {"business.owner_salary": 120000} or {"income.W-2": 150000}
