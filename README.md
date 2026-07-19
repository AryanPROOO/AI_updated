# AI Research Agent

Daily AI research monitoring pipeline with summaries, topic filters, PDF links, and a dashboard UI.

## Architecture

```text
Sources -> Fetcher -> Normalizer -> Dedup -> Classifier -> Summarizer -> Scoring -> PostgreSQL -> Dashboard
```

MVP sources:
- arXiv RSS (cs.AI, cs.CL, cs.LG, cs.RO, cs.CV)
- Hugging Face Daily Papers API

## Quick start (Docker)

```bash
cd ai-research-agent
cp .env.example .env
# Optional: add OPENAI_API_KEY for LLM summaries
docker compose up --build
```

Open:
- Dashboard: http://localhost:3000
- API docs: http://localhost:8000/docs

## Local dev (without full Docker)

### 1. Database

```bash
docker compose up db -d
```

### 2. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql://research:research@localhost:5432/research_agent
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
export NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

## API endpoints

- `GET /api/items?topic=LLM`
- `GET /api/topics`
- `GET /api/stats`
- `POST /api/pipeline/run`
- `GET /api/pipeline/status`

## Phase 2 ideas

- GitHub trending repo detection
- OpenAlex metadata enrichment
- Personalized ranking + feedback loop
- Email/Telegram digest
- Weekly trend graph

## Env vars

See `.env.example`.
