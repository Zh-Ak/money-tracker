from app.database import Base
from sqlalchemy import Column, Integer, String, Numeric, TIMESTAMP, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import Session, relationship, joinedload
from app.schemas import CategoryType
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import calendar
from fastapi import HTTPException

# USER

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, unique=True, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    name = Column(String)
    email = Column(String, unique=True, nullable=False)

class UsersRepository:
    def get_user_by_username(self, db, username) -> User | None:
        return db.query(User).filter(User.username == username).first()
    
    def get_user_by_id(self, db, id) -> User | None:
        return db.query(User).filter(User.id == id).first()

    def get_user_by_email(self, db: Session, email: str):
        return db.query(User).filter(User.email == email).first()

    def add_user(self, db: Session, user_data: dict):
        db_user = User(**user_data)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user


# CATEGORY

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, unique=True, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(Enum(CategoryType), nullable=False)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    transactions = relationship("Transaction", back_populates="category")

class CategoriesRepository():
    def add_category(self, db: Session, user_id, new_category):
        db_category = Category(
            name=new_category.name,
            type=CategoryType.EXPENSE,
            user_id=user_id
        )
        db.add(db_category)
        db.commit()
        db.refresh(db_category)

        return db_category
    
    def get_category_by_id(self, db: Session, category_id: int, user_id: int):
        return db.query(Category).filter(
            Category.id==category_id, 
            Category.user_id==user_id
            ).first()
    
    def get_user_categories(self, db: Session, user_id: int):
        return db.query(Category).filter(Category.user_id == user_id).all()




# TRANSACTION

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, unique=True, primary_key=True, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    description = Column(String)
    created_at = Column(TIMESTAMP, server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(Enum(CategoryType), nullable=False)

    category = relationship("Category", back_populates="transactions")
    
    user = relationship("User")

class TransactionsRepository:
    def add_transaction(self, db: Session, user_id, new_transaction):

        transaction = Transaction(
            amount=new_transaction.amount,
            category_id=new_transaction.category_id,
            type=new_transaction.type,
            description=new_transaction.description,
            user_id= user_id
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
    
        return transaction
    
    def get_all_user_transactions(
        self,
        db: Session,
        user_id: int,
        category_id: int | None = None,
        type: CategoryType | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        limit: int = 10,
        offset: int = 0,
    ):
        query = (
            db.query(Transaction)
            .options(joinedload(Transaction.category))
            .filter(Transaction.user_id == user_id)
            .order_by(Transaction.created_at.desc(), Transaction.id.desc())
        )

        if category_id:
            query = query.filter(Transaction.category_id == category_id)

        if type:
            query = query.filter(Transaction.type == type)

        if date_from:
            query = query.filter(Transaction.created_at >= date_from)

        if date_to:  # inclusive: everything before the start of the next day
            query = query.filter(Transaction.created_at < date_to + timedelta(days=1))

        return query.offset(offset).limit(limit).all()

    def update_transaction(self, db, user_id, transaction_id, transaction_data):
        transaction = db.query(Transaction).filter(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id
        ).first()

        if not transaction:
            return None

        update_data = transaction_data.model_dump(exclude_unset=True)

        new_type = update_data.get("type", transaction.type)
        new_category_id = update_data.get("category_id", transaction.category_id)

        if new_type == CategoryType.EXPENSE:
            if not new_category_id:
                raise HTTPException(status_code=400, detail="Expense requires a category")
            category = db.query(Category).filter(
                Category.id == new_category_id,
                Category.user_id == user_id
            ).first()
            if not category:
                raise HTTPException(status_code=404, detail="Category not found or doesn't belong to you")
        else:
            update_data["category_id"] = None 

        for key, value in update_data.items():
            setattr(transaction, key, value)

        db.commit()
        db.refresh(transaction)

        return transaction

    def delete_transaction(self, db, user_id, transaction_id):
        transaction = db.query(Transaction).filter(
            Transaction.id == transaction_id, 
            Transaction.user_id == user_id
        ).first()
    
        if not transaction:
            return None


        db.delete(transaction)
        db.commit()
        return True

    def get_monthly_category_spendings(self, db: Session, user_id: int):
        now = datetime.now(timezone.utc)
    
        start_of_month = datetime(now.year, now.month, 1)

        _, last_day = calendar.monthrange(now.year, now.month)
        end_of_month = datetime(now.year, now.month, last_day, 23, 59, 59)

        return (
        db.query(
            Transaction.category_id,
            Category.name,
            func.sum(Transaction.amount).label("total_spending")
        )
        .join(Category, Transaction.category_id == Category.id)
        .filter(
            Transaction.user_id == user_id,
            Transaction.type == CategoryType.EXPENSE,
            Transaction.created_at >= start_of_month,
            Transaction.created_at <= end_of_month
        )
        .group_by(Transaction.category_id, Category.name)
        .order_by(func.sum(Transaction.amount).desc())
        .all()
    )

    def get_user_balance(self, db: Session, user_id: int) -> dict:
        results = (
            db.query(
                Transaction.type,
                func.coalesce(func.sum(Transaction.amount), 0).label("total")
            )
            .filter(Transaction.user_id == user_id)
            .group_by(Transaction.type)
            .all()
        )

        total_income = Decimal("0")
        total_expense = Decimal("0")

        for row in results:
            if row.type == CategoryType.INCOME:
                total_income = row.total
            elif row.type == CategoryType.EXPENSE:
                total_expense = row.total

        return {
            "total_income": total_income,
            "total_expense": total_expense,
            "current_balance": total_income - total_expense
        }
