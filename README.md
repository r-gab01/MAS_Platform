# MAS Platform (tesi-AOPaaS)

Progetto di Tesi di Gabriele Richiusa su un servizio di Orchestrazione Agentica low code basato su cloud.

## Prerequisiti
- [Docker](https://www.docker.com/) e Docker Compose
- [Node.js](https://nodejs.org/) (versione 18 o raccomandata) e npm
- (Opzionale) Python 3.12+ se si desidera eseguire il backend fuori da Docker

## Guida all'avvio rapido

### 1. Clonare/Scaricare il repository
Dopo aver fatto il clone (o una fetch) del repository da GitHub, entra nella directory del progetto:
```bash
git clone https://github.com/r-gab01/MAS_Platform.git
cd MAS_Platform
```

### 2. Configurazione Backend e Variabili d'Ambiente 
Il backend richiede un file `.env` per connettersi ai vari provider (Azure, AWS, base dati locale, Ollama, ecc.).

1. Copia il file d'esempio:
   ```bash
   # Dalla root del progetto spostati nella cartella app e copia l'environment
   cd app
   cp example.env .env
   # o su windows: copy example.env .env
   ```
2. Apri il file `app/.env` appena creato e compila le credenziali necessarie (es. API key per i vari LLM, chiavi di Tavily). Se vuoi testare un LLM in locale via Ollama, ricorda di settare `OLLAMA_BASE_URL=http://host.docker.internal:11434` così che il container Docker possa raggiungere l'host. 
3. Torna alla root del progetto:
   ```bash
   cd ..
   ```

### 3. Avvio del Backend e del Database tramite Docker
Esegui il docker-compose dalla **root** del progetto per formare l'infrastruttura base (il database PostgreSQL con estensione `pgvector` e l'istanza del Backend API FastAPI):
```bash
docker-compose up --build -d
```
- Le **API (Backend)** saranno in ascolto su: `http://localhost:8000`
- La documentazione (Swagger) sarà su: `http://localhost:8000/docs`

*(Se non vuoi utilizzare Docker, puoi installare la venv python, installare `pip install -r app/requirements.txt` e lanciare il file `uvicorn app.main:app --reload`)*

### 4. Avvio del Frontend
Dalla **root**, apri una nuova finestra o tab del terminale:
```bash
cd frontend
npm install
npm run dev
```
Questo scaricherà i pacchetti Node necessari per la UI React/Vite e avvierà il processo di sviluppo locale del client Web su cui visualizzare la MAS Platform.