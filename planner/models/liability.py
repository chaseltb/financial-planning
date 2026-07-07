from pydantic import BaseModel

class LiabilityItem(BaseModel):
    id: str
    category: str  # Mortgage, Auto Loan, Credit Cards, Student Loans, Business Loans, Other
    description: str
    value: float
    interest_rate: float = 0.0  # Annual interest rate
    monthly_payment: float = 0.0
