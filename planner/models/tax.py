from pydantic import BaseModel
from typing import List, Dict, Optional

class TaxBracket(BaseModel):
    rate: float
    threshold: float  # Income above this threshold

class TaxRulesModel(BaseModel):
    tax_year: int
    standard_deduction: Dict[str, float]  # E.g. {"single": 16100, "married": 32200}
    brackets: Dict[str, List[TaxBracket]]  # E.g. {"single": [...], "married": [...]}
    corporate_rate: Optional[float] = 0.21
