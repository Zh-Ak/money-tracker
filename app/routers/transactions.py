from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.repository import TransactionsRepository, CategoriesRepository
from app.schemas import CreateTransaction, PostTransaction, TransactionResponse, UpdateTransaction
from app.schemas import CategoryType
from app.security import get_current_user_id

router = APIRouter(prefix="/transactions", tags=["transactions"])
transactions_repo = TransactionsRepository()
categories_repo = CategoriesRepository()


@router.post("", response_model=PostTransaction, status_code=status.HTTP_201_CREATED)
def post_transaction(
    new_transaction: CreateTransaction,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    if new_transaction.type == CategoryType.EXPENSE:
        if not new_transaction.category_id:
            raise HTTPException(status_code=400, detail="For expense category should be chosen")

        category = categories_repo.get_category_by_id(db, new_transaction.category_id, user_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found or doesn't belong to you")
    else:
        new_transaction.category_id = None

    return transactions_repo.add_transaction(db, user_id, new_transaction)


@router.get("", response_model=list[TransactionResponse])
def get_all_transaction(
    category_id: int | None = None,
    type: CategoryType | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=422, detail="date_from must be before date_to")
    return transactions_repo.get_all_user_transactions(
        db,
        user_id,
        category_id=category_id,
        type=type,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )


@router.patch("/{id}", response_model=TransactionResponse)
def patch_transaction(
    id: int,
    transaction: UpdateTransaction,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    updated_tx = transactions_repo.update_transaction(db, user_id, id, transaction)

    if not updated_tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    return updated_tx


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    deleted = transactions_repo.delete_transaction(db, user_id, id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
