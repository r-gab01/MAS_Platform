# MAS Platform (tesi-AOPaaS)

Thesis Project by Gabriele Richiusa on a cloud-based low-code Agent Orchestration service.

## Prerequisites
- [Docker](https://www.docker.com/) and Docker Compose
- [Node.js](https://nodejs.org/) (version 18 or higher recommended) and npm
- (Optional) Python 3.12+ if you wish to run the backend outside of Docker

## Quick Start Guide

### 1. Clone/Download the repository
After cloning (or fetching) the repository from GitHub, navigate to the project directory:
```bash
git clone https://github.com/r-gab01/MAS_Platform.git
cd MAS_Platform
```

### 2. Backend Configuration and Environment Variables
The backend requires an `.env` file to connect to various providers (Azure, AWS, local database, Ollama, etc.).

1. Copy the example environment file:
   ```bash
   # From the project root, navigate to the app folder and copy the environment file
   cd app
   cp example.env .env
   # or on Windows: copy example.env .env
   ```
2. Open the newly created `app/.env` file and fill in the necessary credentials (e.g., API keys for various LLMs, Tavily keys). If you want to test a local LLM via Ollama, remember to set `OLLAMA_BASE_URL=http://host.docker.internal:11434` so that the Docker container can reach the host machine.
3. Return to the project root:
   ```bash
   cd ..
   ```

### 3. Start the Platform via Docker
Run docker-compose from the **root** of the project to build and start the entire infrastructure (Database, Backend API, and Frontend web client):
```bash
docker-compose up --build -d
```
- The **Frontend Web Client** will be accessible at: `http://localhost:3000`
- The **APIs (Backend)** will be listening on: `http://localhost:8000`
- The documentation (Swagger) will be available at: `http://localhost:8000/docs`

*(If you prefer manual setup without Docker, check the specific folders for their traditional python/npm start scripts).*