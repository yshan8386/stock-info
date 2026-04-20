# ysj.brief

개발, 투자, AI 뉴스를 RSS로 수집하고 개인용 데일리 브리핑으로 보여주는 대시보드입니다.

## Stack

- Frontend: Next.js 14, TypeScript, Tailwind CSS
- Backend: FastAPI, SQLAlchemy, PostgreSQL
- Scheduler: APScheduler worker container
- Auth: JWT stored in `httpOnly` cookie

## Local Setup

```bash
cp .env.example .env
docker compose up --build
```

Open:

- Frontend: http://localhost:3000
- Backend health: http://localhost:8000/health
- API docs: http://localhost:8000/docs

## Local Development Without Docker

Backend:

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Feed Validation

```bash
cd backend
python ../scripts/validate_feeds.py
```

## Current Scope

- Signup, login, logout with cookie auth
- Dashboard summary
- Daily briefing with mock generation
- Briefing archive and date detail
- Glossary list and detail pages
- RSS feed seed data and collection service
- Worker scheduler with PostgreSQL advisory lock

