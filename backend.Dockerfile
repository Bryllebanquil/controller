FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy app
COPY controller.py /app/controller.py
COPY main.py /app/main.py

# Expose port
EXPOSE 8080

# Default envs
ENV HOST=0.0.0.0 \
    PORT=8080

CMD ["python", "/app/controller.py"]

