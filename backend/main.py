from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.agent import chat
from backend.analytics import list_transactions
from backend.models import ChatRequest, ChatResponse


app = FastAPI(title="PennyWise AI")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/dashboard")
def dashboard() -> dict:
    """Return all data used by the demo banking-home screen."""
    recent_activity = list_transactions(
        include_logo=True,
        limit=4,
    )
    return {
        "account": {
            "label": "Primary account",
            "name": "Everyday Chequing",
            "number_masked": "•••• 4821",
            "balance": 8416.52,
        },
        "savings_goal": {
            "name": "Weekend in Montréal",
            "saved": 1840.00,
            "target": 2500.00,
            "progress_percent": 74,
        },
        "insight": "Ask PennyWise about your spending, recurring charges, or transactions.",
        "recent_transactions": recent_activity["transactions"],
    }


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    history = [
        {
            "role": message.role,
            "content": message.content,
        }
        for message in request.history
    ]

    response = chat(
        message=request.message,
        history=history,
    )

    return ChatResponse(**response)
