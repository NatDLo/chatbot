# Natichat – Chat Application

A small RAG-style chat app. It provides:
- A FastAPI backend that stores text chunks with OpenAI embeddings in a database and answers questions using retrieved context.
- A simple static frontend with a chat UI and an admin UI to create/list embeddings.

## Project Structure

```
chatbot/
├─ static/
│  ├─ index.html         # Chat UI
│  ├─ admin.html         # Admin UI
│  ├─ chat.js            # Chat page logic (calls /chat/)
│  ├─ admin.js           # Admin page logic (calls /admin/embeddings/*)
│  └─ styles.css         # Styles (optional)
├─ util/
│  ├─ main.py            # FastAPI app entrypoint
│  ├─ routers.py         # API routes (admin + chat)
│  ├─ chatbot.py         # Retrieval + LLM calls
│  ├─ db.py              # SQLAlchemy engine/session
│  └─ models.py          # SQLAlchemy models + Pydantic schemas
├─ requirements.txt
└─ README.md
```

## Prerequisites

- Python 3.10+
- An OpenAI API key

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repo-name>/chatbot
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a .env file from the example and set values:
   ```bash
   cp .env.example .env
   ```
   Required:
   - OPENAI_API_KEY=your_key
     
   Optional (defaults shown):
   - EMBEDDING_MODEL=text-embedding-3-large
   - CHAT_MODEL=gpt-4o-mini
   - DATABASE_URL=sqlite:///./db.sqlite

## Running the app

Run from the util directory so relative imports and static paths resolve correctly:

```bash
cd util
uvicorn main:app --reload
```

Open:
- Chat UI: http://localhost:8000/
- Admin UI: http://localhost:8000/admin

## Usage

- Admin:
  - Go to /admin to create embeddings from your base text.
  - Optionally include a JSON metadata object.

- Chat:
  - Use the chat UI at / to ask questions. The backend retrieves the most similar chunks via cosine similarity and responds with the configured chat model.

## API Endpoints

- Create embedding:
  - POST /admin/embeddings/
  - Body:
    ```json
    {
      "text": "Base text to index",
      "meta": {"location":"Center"}
    }
    ```
  - Response: {"status":"ok","id":<number>}

- List embeddings:
  - GET /admin/embeddings/list
  - Response: [{"id":1,"text":"...","meta":{...}}, ...]

- Chat:
  - POST /chat/
  - Body:
    ```json
    { "text": "Your question" }
    ```
  - Response: {"response":"...answer..."}

Example with curl:
```bash
# Create an embedding
curl -X POST http://localhost:8000/admin/embeddings/ \
  -H "Content-Type: application/json" \
  -d '{"text":"Apartment with 2 bedrooms near downtown","meta":{"city":"CABA"}}'

# Ask a question
curl -X POST http://localhost:8000/chat/ \
  -H "Content-Type: application/json" \
  -d '{"text":"Do you have 2-bedroom apartments downtown?"}'
```

## Troubleshooting

- 404 or import errors when starting:
  - Ensure you run uvicorn from chatbot/util: `cd chatbot/util && uvicorn main:app --reload`.
- OpenAI errors:
  - Verify OPENAI_API_KEY in your .env and network access.
- SQLite file location:
  - Default is util/db.sqlite (controlled by DATABASE_URL).

## Contributing

Issues and pull requests are welcome.

## License


MIT
