from pydantic import BaseModel

class IncomeItem(BaseModel):
    id: str
    category: str  # W-2, 1099, Business Distribution, Interest, Dividends, Capital Gains, Rental Income, Other
    description: str
    amount: float
    frequency: str = "Annual"  # Quarterly, Annual
    taxable: bool = True
