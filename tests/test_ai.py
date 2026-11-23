from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers import ai
from app.database import get_db
from app.security import get_current_user_id


class FakeModels:
    def __init__(self, text="Cut food spending 🍕", error=None):
        self.text, self.error, self.calls = text, error, []

    def generate_content(self, model, contents, **kwargs):
        self.calls.append(contents)
        if self.error:
            raise self.error
        return SimpleNamespace(text=self.text)


class FakeClient:
    def __init__(self, **kwargs):
        self.models = FakeModels(**kwargs)


STATS = [SimpleNamespace(name="Food", total_spending=Decimal("95000.00"))]
BALANCE = {"total_income": Decimal("450000.00"),
           "total_expense": Decimal("330000.00"),
           "current_balance": Decimal("120000.00")}


@pytest.fixture
def client(monkeypatch):
    app.dependency_overrides[get_current_user_id] = lambda: 1
    app.dependency_overrides[get_db] = lambda: None          # no real DB
    monkeypatch.setattr(ai.transactions_repo, "get_monthly_category_spendings", lambda db, uid: STATS)
    monkeypatch.setattr(ai.transactions_repo, "get_user_balance", lambda db, uid: BALANCE)
    yield TestClient(app)
    app.dependency_overrides.clear()


def use_fake(monkeypatch, fake):
    monkeypatch.setattr(ai, "get_gemini_client", lambda: fake)
    return fake


def test_returns_advice_and_sends_user_data(client, monkeypatch):
    fake = use_fake(monkeypatch, FakeClient())
    r = client.post("/ai/chat", json={"prompt": "Why is food so high?"})
    assert r.status_code == 200
    assert r.json() == {"recommendation": "Cut food spending 🍕"}
    sent = fake.models.calls[0]
    assert "- Food: 95000.00 KZT" in sent
    assert "Why is food so high?" in sent


def test_no_expenses_skips_gemini(client, monkeypatch):
    fake = use_fake(monkeypatch, FakeClient())
    monkeypatch.setattr(ai.transactions_repo, "get_monthly_category_spendings", lambda db, uid: [])
    r = client.post("/ai/chat")
    assert r.status_code == 200
    assert fake.models.calls == []


def test_rate_limit_becomes_429(client, monkeypatch):
    use_fake(monkeypatch, FakeClient(error=Exception("429 RESOURCE_EXHAUSTED")))
    assert client.post("/ai/chat").status_code == 429


def test_other_error_becomes_502(client, monkeypatch):
    use_fake(monkeypatch, FakeClient(error=Exception("boom")))
    assert client.post("/ai/chat").status_code == 502


def test_missing_key_becomes_503(client, monkeypatch):
    monkeypatch.setattr(ai, "_gemini_client", None)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert client.post("/ai/chat").status_code == 503


def test_prompt_too_long_is_422(client, monkeypatch):
    use_fake(monkeypatch, FakeClient())
    assert client.post("/ai/chat", json={"prompt": "x" * 501}).status_code == 422