# Inicialización de la aplicación FastAPI, incluyendo routers para chat y embeddings
import sys
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from util.db import init_db
from util.routers import router, chatbot
from util.chatbot import ChatbotEmpresa
from pathlib import Path


# BASE_DIR = raíz del proyecto (carpeta chatbot)
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR / "util"))
app = FastAPI(title="Natichat")

# Crear DB
init_db()

# cargar datos desde la DB
try:
    chatbot.cargar_informacion_empresa({})
except Exception as e:
    print("No se pudieron cargar embeddings al inicio:", e)

# Montar static
STATIC_DIR = BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Incluir routers
app.include_router(router)

# Servir HTML desde static
@app.get("/admin")
def admin_page():
    return FileResponse("../static/admin.html")

@app.get("/")
def chat_page():
    return FileResponse("../static/index.html")
