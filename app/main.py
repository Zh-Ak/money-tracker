from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.routers import auth, users, transactions, categories, statistics, ai

app = FastAPI(title="Money Tracker API")


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(transactions.router)
app.include_router(categories.router)
app.include_router(statistics.router)
app.include_router(ai.router)


@app.get("/")
async def serve_index():
    return FileResponse("static/index.html")


@app.get("/health")
async def health_check():
    return {"status": "ok"}
