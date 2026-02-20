FROM node:20-alpine AS ui-builder
WORKDIR /ui
COPY ["agent-controller ui v2.1/package.json", "/ui/package.json"]
COPY ["agent-controller ui v2.1/vite.config.ts", "/ui/vite.config.ts"]
COPY ["agent-controller ui v2.1/index.html", "/ui/index.html"]
COPY ["agent-controller ui v2.1/src", "/ui/src"]
COPY ["agent-controller ui v2.1/styles", "/ui/styles"]
COPY ["agent-controller ui v2.1/index.css", "/ui/index.css"]
RUN npm install --no-audit --no-fund
RUN npm run build

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
COPY requirements-controller.txt /app/requirements-controller.txt
RUN if [ -f /app/requirements.txt ]; then pip install --no-cache-dir -r /app/requirements.txt; fi
RUN pip install --no-cache-dir -r /app/requirements-controller.txt

COPY controller.py /app/controller.py
COPY main.py /app/main.py

COPY --from=ui-builder /ui/build "/app/agent-controller ui v2.1/build"

EXPOSE 8080

ENV HOST=0.0.0.0 \
    PORT=8080

CMD ["gunicorn", "-k", "geventwebsocket.gunicorn.workers.GeventWebSocketWorker", "-w", "1", "--bind", "0.0.0.0:8080", "controller:app"]
