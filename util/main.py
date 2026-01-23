# Initialize the app and configure routes and static files
import sys
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from util.db import init_db
from util.routers import router, chatbot
from util.chatbot import CompanyChatbot
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent  # folder chatbot/
sys.path.append(str(ROOT / "util"))

app = FastAPI(title="Natichat")

# Create DB
init_db()

# Load data from DB
try:
    chatbot.load_company_information({})
except Exception as e:
    print("Failed to load embeddings at startup:", e)

# Mount static
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

# Include routers
app.include_router(router)

# Serve HTML from static
@app.get("/admin")
def admin_page():
    return FileResponse(ROOT / "static" / "admin.html")

@app.get("/")
def chat_page():
    return FileResponse(ROOT / "static" / "index.html")
