# chatbot.py
import json
import math
import pickle
import os
import re
import difflib
import unicodedata
from dotenv import load_dotenv
from datetime import datetime
from util.db import SessionLocal
from util.models import Conversation
from openai import OpenAI
from typing import List, Dict

# Carga variables del .env automáticamente
load_dotenv()

# Configuración
API_KEY = os.getenv("OPENAI_API_KEY")  # Usa tu API key
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ChatbotEmpresa:
    def __init__(self, nombre_empresa: str):
        self.nombre_empresa = nombre_empresa
        self.contexto_base = ""
        self.base_conocimiento = []
        self.embeddings_conocimiento = []

    def normalizar_texto(self, texto: str) -> str:
        """
        Normaliza el texto para mejorar la consistencia en búsquedas
        y comparaciones (minúsculas, sin acentos).
        """
        texto = texto.lower()
        texto = ''.join(
            c for c in unicodedata.normalize('NFD', texto)
            if unicodedata.category(c) != 'Mn'
        )
        return texto
        
    def cargar_informacion_empresa(self, archivos: Dict[str, str]):
        """
        Carga la información específica de la empresa desde la base de datos.
        Los registros en DB ya están chunkeados y con sus embeddings en vector.
        """
        print("Cargando información de la empresa (DB)...")

        from db import SessionLocal
        from models import Embedding

        textos: List[str] = []
        vectores: List[List[float]] = []

        session = SessionLocal()
        try:
            registros = session.query(Embedding).all()
            if not registros:
                print("No hay registros en la tabla embeddings")
            else:
                for r in registros:
                    texto = (r.text or "").strip()
                    if not texto:
                        continue

                    vector = r.vector
                    if isinstance(vector, list):
                        v = vector
                    elif isinstance(vector, str):
                        # defensa por si el JSON estuvo serializado como string
                        try:
                            parsed = json.loads(vector)
                            v = parsed if isinstance(parsed, list) else []
                        except Exception:
                            v = []
                    else:
                        v = []

                    textos.append(texto)
                    vectores.append(v)

                print(f"{len(textos)} entradas cargadas desde DB")

            # Usar directamente los chunks y sus vectores persistidos
            self.base_conocimiento = textos
            self.embeddings_conocimiento = vectores
            self.contexto_base = "\n\n".join(textos)

            con_vec = sum(1 for v in self.embeddings_conocimiento if isinstance(v, list) and v)
            print(f"Información lista: {len(self.base_conocimiento)} entradas, {con_vec} con embeddings")
        finally:
            session.close()
        
    def _dividir_en_chunks(self, texto: str, oraciones_por_chunk: int = 2) -> list:
        oraciones = re.split(r'(?<=[.!?])\s+', texto)
        oraciones = [o.strip() for o in oraciones if o.strip()]

        chunks = [" ".join(oraciones[i:i+oraciones_por_chunk]) for i in range(0, len(oraciones), oraciones_por_chunk)]
        chunks = [self.normalizar_texto(c) for c in chunks] 

        return chunks
                
    def crear_embeddings(self):
        """
        Crea embeddings para la base de conocimiento
        """
        print("Creando embeddings...")
        
        self.embeddings_conocimiento = []
        
        for chunk in self.base_conocimiento:
            embedding = self._obtener_embedding(chunk)
            self.embeddings_conocimiento.append(embedding)
            
        print("Embeddings creados correctamente")
    
    def _obtener_embedding(self, text: str) -> List[float]:
        """
        Obtiene el embedding de un texto usando OpenAI
        """
        resp = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return resp.data[0].embedding
    
    def _calcular_similitud(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calcula la similitud coseno entre dos vectores de embeddings
        """
        dot = sum(x*y for x,y in zip(vec1, vec2))
        na = sum(x*x for x in vec1)**0.5
        nb = sum(y*y for y in vec2)**0.5
        if na==0 or nb==0:
            return 0.0
        return dot/(na*nb)
    
    def buscar_informacion_relevante(self, pregunta: str, top_n: int = 3) -> str:
        """
        Busca la información más relevante en la base de conocimiento
        usando similitud coseno con el embedding de la pregunta.
        """
        pregunta = self.normalizar_texto(pregunta)
        embedding_pregunta = self._obtener_embedding(pregunta)
        
        # calcular similitudes
        similitudes = [(self._calcular_similitud(embedding_pregunta, e), i) 
                    for i, e in enumerate(self.embeddings_conocimiento)]
        
        similitudes.sort(reverse=True, key=lambda x: x[0])
        
        informacion_relevante = []
        for similitud, indice in similitudes[:top_n]:
            if similitud > 0.1:  # <- ajuste de umbral, mas chico mas flexible, para contemplar tmb errores ortograficos
                informacion_relevante.append(self.base_conocimiento[indice])
        
        return "\n\n".join(informacion_relevante)

    
    def responder_pregunta(self, pregunta: str, historial: List[Dict] = None) -> str:
        """
        Genera una respuesta como si fuera un operador
        """
        # Buscar información relevante
        contexto = self.buscar_informacion_relevante(pregunta)
        
        # Preparar el prompt
        prompt = f"""
        Eres un operador de atención al cliente de {self.nombre_empresa}.
        Tu tono debe ser profesional, amable y servicial.
        
        INFORMACIÓN DE LA EMPRESA:
        {contexto}
        
        HISTORIAL DE CONVERSACIÓN (si aplica):
        {historial if historial else 'Primera consulta'}
        
        PREGUNTA DEL CLIENTE:
        {pregunta}
        
        INSTRUCCIONES:
        1. Responde basándote ÚNICAMENTE en la información proporcionada
        2. Si la respuesta no está en la información, di: "No tengo esa información específica, pero puedo contactarte con el departamento correspondiente"
        3. Sé conciso pero completo
        4. Mantén un tono amable y profesional
        5. Ofrece ayuda adicional si es apropiado
        
        RESPUESTA:
        """
        
        # Generar respuesta
        resp = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": prompt}
            ],
            temperature=0.3
        )
        return resp.choices[0].message.content
    
    def guardar_conversacion(self, usuario: str, conversacion: list):
        """
        Guarda la conversación en la base de datos usando el modelo Conversation.
        """
        db = SessionLocal()
        try:
            nueva_conversacion = Conversation(
                usuario=usuario,
                conversacion=conversacion,
                created_at=datetime.now()
            )
            db.add(nueva_conversacion)
            db.commit()
            db.refresh(nueva_conversacion)
            print(f"Conversación de {usuario} guardada en DB (id={nueva_conversacion.id})")
        except Exception as e:
            db.rollback()
            print(f"Error guardando conversación: {e}")
        finally:
            db.close()
