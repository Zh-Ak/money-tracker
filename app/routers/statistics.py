from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.repository import TransactionsRepository
from app.schemas import Statistics
from app.security import get_current_user_id

router = APIRouter(prefix="/statistics", tags=["statistics"])
transactions_repo = TransactionsRepository()


@router.get("/monthly", response_model=list[Statistics])
def get_statistics(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return transactions_repo.get_monthly_category_spendings(db, user_id)
