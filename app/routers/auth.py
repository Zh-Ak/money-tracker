from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.repository import UsersRepository
from app.schemas import UserCreate
from app.security import hash_password, verify_password, create_jwt

router = APIRouter(prefix="/auth", tags=["auth"])
users_repo = UsersRepository()


@router.post("/register", status_code=status.HTTP_201_CREATED)
def post_registration(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = users_repo.get_user_by_username(db, user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    if user.email:
        existing_email = users_repo.get_user_by_email(db, user.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    hashed_pwd = hash_password(user.password)
    user_data = user.model_dump()
    user_data["password"] = hashed_pwd

    try:
        users_repo.add_user(db, user_data)
    except IntegrityError:
        # Two requests with the same username/email at the same moment:
        # both pass the checks above, the database unique constraint stops the second.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered",
        )
    return {"message": "User registered successfully"}


@router.post("/login")
def post_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = users_repo.get_user_by_username(db, form_data.username)

    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_jwt(user.id)
    return {"access_token": token, "token_type": "bearer"}
