# Usamos Python 3.11 (elige la versión compatible con tu proyecto)
FROM python:3.11-slim

# Establecemos el directorio de trabajo
WORKDIR /app

# Copiamos requirements y los instalamos primero (para aprovechar cache)
COPY requirements.txt .

RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir --only-binary=:all: -r requirements.txt

# Copiamos todo el proyecto
COPY . .

# Exponemos el puerto que uvicorn usará
EXPOSE 8000

# Comando de inicio
CMD ["uvicorn", "util.main:app", "--host", "0.0.0.0", "--port", "8000"]
