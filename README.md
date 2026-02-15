Neural Control Hub

Overview
- A legitimate, authorization-based remote device management dashboard.
- Frontend: React + Vite TypeScript using Radix UI components.
- Backend: Flask + Socket.IO or FastAPI + WebSockets for low-latency event delivery.
- Streaming: WebRTC/HLS viewers with adaptive quality.
- Storage: Redis for routing/queues; SQLite for lightweight state.

Key Features
- Agents list with online/offline status and capabilities.
- Command panel with correlated, asynchronous results.
- File manager with safe previews (images, video, pdf) and downloads/uploads.
- Streaming viewer with low-latency transport and fallback modes.
- Activity feed and system monitoring (latency, throughput, command stats).

Architecture
- Control plane: WebSockets for controller↔server and agent↔server; no polling.
- Data plane: Streams routed via server; controller is not in the critical path.
- Event model: Commands carry command_id; server ACKs immediately; results arrive asynchronously.
- Queueing: Redis used for message routing and temporary buffering.
- Adaptation: Heartbeats inform RTT/jitter; streams and batching adjust automatically.

Tech Stack
- Frontend: React 18, Vite 6, TypeScript 5, Radix UI, Tailwind utilities, Socket.IO client.
- Backend: Flask 3 + Flask-SocketIO or FastAPI 0.104 + Uvicorn.
- Messaging: Redis 7.
- Build/Deploy: Docker, Render-compatible server, Docker Compose for local dev.

Prerequisites
- Node.js >= 20.10.0
- Python 3.12.x
- Redis 7.x
- Modern browser (Chrome/Edge latest) with WebRTC support

Quick Start (Frontend)
- cd "agent-controller ui v2.1"
- npm install
- npm run dev  (development)
- npm run build (production build in /build)

Quick Start (Backend: Flask + Socket.IO)
- python -m venv .venv && source .venv/Scripts/activate  (Windows PowerShell)
- pip install -r requirements-controller.txt
- set FLASK_APP=controller.py
- set SECRET_KEY=change_me
- set REDIS_URL=redis://localhost:6379
- python controller.py

Quick Start (Backend: FastAPI + WebSockets)
- python -m venv .venv && source .venv/Scripts/activate
- pip install -r requirements-fastapi.txt
- set REDIS_URL=redis://localhost:6379
- uvicorn fastapi_server:app --host 0.0.0.0 --port 8000

Docker Compose (Local)
- docker compose up --build
- Services: redis:6379, fastapi-server:8000
- Configure your frontend API base URL to point at http://localhost:8000

Configuration
- API_URL: Base URL for the backend API.
- REDIS_URL: Redis connection string (e.g., redis://localhost:6379).
- SECRET_KEY: Session/signing secret (do not commit).
- AUTH: Optional TOTP and session configuration under /api/auth.
- Tests: Some tests require ADMIN_PASSWORD to be set before controller import.

Deployment (Render-friendly)
- Build a backend service (Flask or FastAPI) with a dedicated web port.
- Use a Redis add-on or a managed Redis instance.
- Deploy the frontend as static (Vite build output) via a static site service or CDN.
- Ensure WebSocket endpoints are exposed; keep-alives enabled.
- Scale streams and commands independently to avoid contention.

Security & Compliance
- For authorized remote administration only. Obtain explicit consent and follow local laws and organizational policies.
- Do not use this software to access or control devices without permission.
- Protect secrets via environment variables and secret managers; never commit credentials.
- Harden server (rate limits, CORS, CSRF/session configs, TLS).

Accessibility
- Uses Radix UI primitives with proper roles/labels.
- Dialogs include DialogTitle and DialogDescription for screen readers.
- Toggle and inputs include ARIA attributes where applicable.

Project Structure (High Level)
- agent-controller ui v2.1/: React/Vite TypeScript UI
- controller.py: Flask + Socket.IO backend
- fastapi_server.py: FastAPI WebSocket backend (low-latency option)
- docker-compose.yml: Local dev services (Redis + server)
- requirements-*.txt: Dependency sets per backend mode
- deploy/: Nginx and deployment configs

Development Tips
- Keep commands event-driven; never block the UI waiting for execution.
- Use correlation IDs and timeouts (e.g., 15s TTL) for command lifecycle.
- Route streams via server; avoid direct agent→controller transport.
- Implement retries at the delivery/work layer, not by UI resends.
- Measure RTT/jitter via heartbeats and adapt stream bitrate/FPS accordingly.

Contributing
- Open issues with clear reproduction steps.
- Propose PRs that maintain accessibility, security, and separation of concerns.
- Follow Node/TypeScript and Python formatting/linting guidelines.

License
- Specify your license here (e.g., MIT). Add a LICENSE file if applicable.

