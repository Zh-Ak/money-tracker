import logging
import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from google import genai

from app.database import get_db
from app.repository import TransactionsRepository
from app.schemas import AIChatRequest
from app.security import get_current_user_id

router = APIRouter(prefix="/ai", tags=["ai"])
logger = logging.getLogger(__name__)
transactions_repo = TransactionsRepository()

_gemini_client = None

def get_gemini_client():
    global _gemini_client
    if _gemini_client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=503, detail="AI service is not configured")
        _gemini_client = genai.Client(api_key=api_key)
    return _gemini_client

@router.post("/chat")
def get_ai_financial_advice(
    body: AIChatRequest | None = None,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    client = get_gemini_client()
    stats = transactions_repo.get_monthly_category_spendings(db, user_id)
    balance = transactions_repo.get_user_balance(db, user_id)

    if not stats:
        return {"recommendation": "You don't have enough expenses this month for an analysis yet."}

    summary = f"Current balance: {balance['current_balance']} KZT.\n"
    summary += f"Total income: {balance['total_income']} KZT, total expenses: {balance['total_expense']} KZT.\n"
    summary += "Spending by category this month:\n"

    for item in stats:
        summary += f"- {item.name}: {item.total_spending} KZT\n"

    prompt = f"""
    You are a professional but friendly financial advisor.
    Analyze the following financial data of the user:
    {summary}
    Give a short overview (2-3 sentences) and 2 concrete, practical tips
    on how to reduce spending. Keep it short and clear, use emoji, and avoid jargon.
    Answer in English.
    """

    question = body.prompt.strip() if body and body.prompt else ""
    if question:
        prompt += f"""
    The user also asked this question. Answer it using their data above:
    {question}
    """

    try:
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=prompt,
        )
        return {"recommendation": response.text}
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            raise HTTPException(
                status_code=429, 
                detail="AI request limit reached. Please wait a minute and try again."
            )
        logger.exception("Gemini request failed")
        raise HTTPException(status_code=502, detail="Could not get advice from the AI. Please try again later.")
