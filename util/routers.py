from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db import get_db
from models import Embedding, EmbeddingCreate, ChatRequest
from chatbot import ChatbotEmpresa

router = APIRouter()

# Inicializar el chatbot
chatbot = ChatbotEmpresa(nombre_empresa="Mi Empresa")

# --- ADMIN ---
@router.post("/admin/embeddings/")
def create_embedding(embedding: EmbeddingCreate, db: Session = Depends(get_db)):
    vector = chatbot._obtener_embedding(embedding.text)
    emb = Embedding(text=embedding.text, vector=vector, meta=embedding.meta)
    db.add(emb)
    db.commit()
    db.refresh(emb)
    # cargar datos desde la DB
    try:
        chatbot.cargar_informacion_empresa({})
    except Exception as e:
        print("No se pudieron cargar embeddings al inicio:", e)
    return {"status": "ok", "id": emb.id}

@router.get("/admin/embeddings/list")
def list_embeddings(db: Session = Depends(get_db)):
    embeddings = db.query(Embedding).all()
    return [{"id": e.id, "text": e.text, "meta": e.meta} for e in embeddings]

# --- CHAT ---
@router.post("/chat/")
def chat_endpoint(request: ChatRequest):
    respuesta = chatbot.responder_pregunta(request.text)
    return {"response": respuesta}