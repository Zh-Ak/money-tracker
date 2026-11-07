from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.repository import UsersRepository, TransactionsRepository
from app.schemas import Balance, Profile
from app.security import get_current_user_id

router = APIRouter(prefix="/users", tags=["users"])
users_repo = UsersRepository()
transactions_repo = TransactionsRepository()


@router.get("/me", response_model=Profile)
def get_profile(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    user = users_repo.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


@router.get("/me/balance", response_model=Balance)
def get_balance(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return transactions_repo.get_user_balance(db, user_id)
