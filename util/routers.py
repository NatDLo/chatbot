from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from util.db import get_db
from util.models import Embedding, EmbeddingCreate, ChatRequest
from util.chatbot import ChatbotEmpresa

router = APIRouter()

# Initialize chatbot instance
chatbot = ChatbotEmpresa(company="My Company")

# --- ADMIN ---
@router.post("/admin/embeddings/")
def create_embedding(embedding: EmbeddingCreate, db: Session = Depends(get_db)):
    vector = chatbot._obtain_embedding(embedding.text)
    emb = Embedding(text=embedding.text, vector=vector, meta=embedding.meta)
    db.add(emb)
    db.commit()
    db.refresh(emb)
    # load data from DB
    try:
        chatbot.load_company_information({})
    except Exception as e:
        print("Failed to load embeddings at startup:", e)
    return {"status": "ok", "id": emb.id}

@router.get("/admin/embeddings/list")
def list_embeddings(db: Session = Depends(get_db)):
    embeddings = db.query(Embedding).all()
    return [{"id": e.id, "text": e.text, "meta": e.meta} for e in embeddings]

# --- CHAT ---
@router.post("/chat/")
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    chatbot.load_company_information({})  # reload from DB
    response = chatbot.answer_question(request.text)
    return {"response": response}