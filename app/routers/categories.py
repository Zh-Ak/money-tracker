from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.repository import CategoriesRepository
from app.schemas import CategoryCreate, CategoryResponse
from app.security import get_current_user_id

router = APIRouter(prefix="/categories", tags=["categories"])
categories_repo = CategoriesRepository()


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def post_category(
    new_category: CategoryCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return categories_repo.add_category(db, user_id, new_category)


@router.get("", response_model=list[CategoryResponse])
def get_categories(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return categories_repo.get_user_categories(db, user_id)
