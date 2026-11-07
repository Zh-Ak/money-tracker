from decimal import Decimal

from pydantic import BaseModel, EmailStr, ConfigDict, Field

from enum import Enum
from typing import Annotated

# Money is Decimal, never float: floats can't store most decimal fractions exactly
# (0.1 + 0.2 == 0.30000000000000004). Max 10 digits before the point, 2 after.
Money = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]


class CategoryType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"

class UserCreate(BaseModel):
    username: str
    password: str 
    name: str
    email: EmailStr


class Profile(BaseModel):
    username: str
    name: str
    email: EmailStr
    
class CategoryCreate(BaseModel):
    name: str

class CategoryResponse(BaseModel):
    id: int
    name: str
    type: CategoryType

class CreateTransaction(BaseModel):
    amount: Money
    category_id: int | None = None
    type: CategoryType
    description : str

class PostTransaction(BaseModel):
    id: int

class TransactionCategoryResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class TransactionResponse(BaseModel):
    id: int
    amount: Decimal
    description: str
    type: CategoryType
    category_id: int | None = None
    category: TransactionCategoryResponse | None = None 

    class Config:
        from_attributes = True

class UpdateTransaction(BaseModel):
    amount: Money | None = None
    description: str | None = None
    type: CategoryType | None = None
    category_id: int | None = None

class Statistics(BaseModel):
    name: str
    total_spending: Decimal

    model_config = ConfigDict(from_attributes=True)


class AIChatRequest(BaseModel):
    prompt: str | None = Field(default=None, max_length=500)


class Balance(BaseModel):
    total_income: Decimal
    total_expense: Decimal
    current_balance: Decimal
