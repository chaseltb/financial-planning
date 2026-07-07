from pydantic import BaseModel

class BusinessProfile(BaseModel):
    name: str = "My Business"
    entity_type: str = "Sole Proprietorship"  # Sole Proprietorship, Single-member LLC, Multi-member LLC, S Corporation, C Corporation
    revenue_growth: float = 0.05  # Quarterly revenue growth expectation
    expense_growth: float = 0.03  # Quarterly expense growth expectation
    owner_salary: float = 50000.0  # Annual salary paid to owner (W-2, especially S-Corp / C-Corp)
    distributions: float = 20000.0  # Annual distributions paid to owner (S-Corp / Partnerships)
