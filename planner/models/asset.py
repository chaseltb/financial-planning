from pydantic import BaseModel

class AssetItem(BaseModel):
    id: str
    category: str  # Cash, Brokerage, Retirement, Real Estate, Vehicles, Business Ownership, Crypto, Other
    description: str
    value: float
    growth_rate: float = 0.05  # Annual expected growth rate
