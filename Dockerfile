# We use the official Python slim image as base
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy requirements and install them first (to leverage cache)
COPY requirements.txt .

RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir --only-binary=:all: -r requirements.txt

# Copy the entire project
COPY . .

# Expose the port that uvicorn will use
EXPOSE 8000

# Start command
CMD ["uvicorn", "util.main:app", "--host", "0.0.0.0", "--port", "8000"]
