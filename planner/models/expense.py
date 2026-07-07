from pydantic import BaseModel

class ExpenseItem(BaseModel):
    id: str
    category: str  # Housing, Food, Healthcare, Utilities, Entertainment, Taxes, Other
    description: str
    amount: float
    frequency: str = "Annual"  # Quarterly, Annual
