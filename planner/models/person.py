from pydantic import BaseModel

class PersonProfile(BaseModel):
    filing_status: str = "single"  # single, married
    retirement_401k: float = 0.0
    retirement_ira: float = 0.0
    retirement_hsa: float = 0.0
    solo_401k: float = 0.0
    sep_ira: float = 0.0
    roth_ira: float = 0.0
