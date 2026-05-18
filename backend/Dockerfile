FROM python:3.11-slim

WORKDIR /app

# System deps + LibreOffice for PPT/DOCX → PDF conversion
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libmagic1 \
    libreoffice \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
