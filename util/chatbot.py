import json
import math
import pickle
import os
import re
import difflib
import unicodedata
from dotenv import load_dotenv
from datetime import datetime
from util.db import LocalSession
from util.models import Conversation, Embedding
from openai import OpenAI
from typing import List, Dict

# bring in environment variables
load_dotenv()

# Configuration
API_KEY = os.getenv("OPENAI_API_KEY")  # Use your API key
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class CompanyChatbot:
    def __init__(self, company: str):
        self.company = company
        self.base_context = ""
        self.knowledge_base = []
        self.knowledge_embeddings = []

    def normalize_text(self, text: str) -> str:
        """
        Normalizes the text to improve consistency in searches
        and comparisons (lowercase, without accents).
        """
        text = text.lower()
        text = ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        )
        return text
        
    def load_company_information(self, files: Dict[str, str]):
        """
        Loads company-specific information from the database.
        Records in DB are already chunked and have their embeddings in vector form.
        """

        texts: List[str] = []
        vectors: List[List[float]] = []

        session = LocalSession()
        try:
            records = session.query(Embedding).all()
            if not records:
                print("No records in the embeddings table.")
            else:
                for r in records:
                    text = (r.text or "").strip()
                    if not text:
                        continue

                    vector = r.vector
                    if isinstance(vector, list):
                        v = vector
                    elif isinstance(vector, str):
                        # defense in case the JSON was serialized as a string
                        try:
                            parsed = json.loads(vector)
                            v = parsed if isinstance(parsed, list) else []
                        except Exception:
                            v = []
                    else:
                        v = []

                    texts.append(text)
                    vectors.append(v)

                print(f"{len(texts)} entries loaded from DB")

            # Use directly the chunks and their persisted vectors
            self.knowledge_base = texts
            self.knowledge_embeddings = vectors
            self.base_context = "\n\n".join(texts)

            con_vec = sum(1 for v in self.knowledge_embeddings if isinstance(v, list) and v)
            print(f"Information ready: {len(self.knowledge_base)} entries, {con_vec} with embeddings")
        finally:
            session.close()
        
    def _separate_in_chunks(self, text: str, sentences_per_chunk: int = 2) -> list:
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        chunks = [" ".join(sentences[i:i+sentences_per_chunk]) for i in range(0, len(sentences), sentences_per_chunk)]
        chunks = [self.normalize_text(c) for c in chunks] 

        return chunks
                
    def create_embeddings(self):
        """
        Creates embeddings for the knowledge base
        """
        print("Creating embeddings...")
        
        self.knowledge_embeddings = []
        
        for chunk in self.knowledge_base:
            embedding = self._obtain_embedding(chunk)
            self.knowledge_embeddings.append(embedding)
            
        print("Embeddings created successfully")
    
    def _obtain_embedding(self, text: str) -> List[float]:
        """
        Obtains the embedding of a text using OpenAI
        """
        resp = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return resp.data[0].embedding
    
    def _calculate_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculates the cosine similarity between two embedding vectors
        """
        dot = sum(x*y for x,y in zip(vec1, vec2))
        na = sum(x*x for x in vec1)**0.5
        nb = sum(y*y for y in vec2)**0.5
        if na==0 or nb==0:
            return 0.0
        return dot/(na*nb)
    
    def search_relevant_information(self, question: str, top_n: int = 3) -> str:
        """
        Searches for the most relevant information in the knowledge base
        using cosine similarity with the embedding of the question.
        """
        question = self.normalize_text(question)
        embedding_question = self._obtain_embedding(question)
        
        # calculate similarities
        similarities = [(self._calculate_similarity(embedding_question, e), i) 
                    for i, e in enumerate(self.knowledge_embeddings)]
        
        similarities.sort(reverse=True, key=lambda x: x[0])
        
        relevant_information = []
        for similarity, index in similarities[:top_n]:
            if similarity > 0.1:  # <- threshold adjustment, smaller but more flexible, to also consider spelling errors
                relevant_information.append(self.knowledge_base[index])
        
        return "\n\n".join(relevant_information)

    
    def answer_question(self, question: str, history: List[Dict] = None) -> str:
        """
        Generates an answer as if it were an operator of customer service
        for the specified company, using relevant information from the knowledge base.
        """
        # Search for relevant information
        context = self.search_relevant_information(question)
        
        # Prepare the prompt
        prompt = f"""
        You are a customer service operator for {self.company}.
        Your tone should be professional, kind, and helpful.
        
        COMPANY INFORMATION:
        {context}
        
        CONVERSATION HISTORY (if applicable):
        {history if history else 'First query'}
        
        CUSTOMER QUESTION:
        {question}
        
        INSTRUCTIONS:
        1. Respond based ONLY on the provided information
        2. If the answer is not in the information, say: "I don't have that specific information, but I can connect you with the appropriate department"
        3. Be concise but complete
        4. Maintain a kind and professional tone
        5. Offer additional help if appropriate
        
        ANSWER:
        """
        
        # Generate answer
        resp = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": prompt}
            ],
            temperature=0.3
        )
        return resp.choices[0].message.content
    
    def save_conversation(self, user: str, conversation: list):
        """
        Saves the conversation in the database using the Conversation model.
        """
        db = LocalSession()
        try:
            new_conversation = Conversation(
                user=user,
                conversation=conversation,
                created_at=datetime.now()
            )
            db.add(new_conversation)
            db.commit()
            db.refresh(new_conversation)
            print(f"Conversation from {user} saved in DB (id={new_conversation.id})")
        except Exception as e:
            db.rollback()
            print(f"Error saving conversation: {e}")
        finally:
            db.close()



