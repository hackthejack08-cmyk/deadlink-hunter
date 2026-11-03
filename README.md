# DeadLink Hunter

**Detect. Diagnose. Fix.** A React frontend with a FastAPI crawler and SQLite scan history.

## Quick start (Windows PowerShell)
```powershell
cd deadlink-hunter
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
npm install
Copy-Item .env.example .env

# terminal 1
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8001

# terminal 2, from the repository root
npm run dev
```

Open `http://localhost:5173`. Run `npm run build` and
`.\.venv\Scripts\python.exe -m pytest -q backend` before deployment.

## Deploy

1. Create the backend on Render from `render.yaml`. Set `DLH_CORS_ORIGINS` to
   the final frontend URL.
2. Import the repository into Vercel. Set `VITE_API_URL` to the Render service
   URL, then deploy.

`vercel.json` keeps React Router URLs working when opened directly. Render's
free filesystem is temporary, so add a persistent disk before relying on scan
history.

## Tech stack
React 18, TypeScript, Vite, Tailwind CSS, React Router 6, Framer Motion, Recharts, React Flow (`@xyflow/react`), Lucide.

## Structure
`src/services` (API + mock adapters), `src/hooks/useScan.ts` (polling state machine), `src/types` (contracts), `src/data/demoData.ts` (all mock data, clearly labelled DEMO in the UI), `src/components/animations` (MechanicalScanner, TextDropHero).

## Backend contract
Base URL = `VITE_API_URL`. All bodies are JSON; types live in `src/types/scan.ts`.

| Method | Path | Body | Returns |
|---|---|---|---|
| POST | `/scans` | `ScanRequest {url, maxDepth?, checkExternal?}` | `ScanJob` |
| GET | `/scans` | | `ScanJob[]` (newest first) |
| GET | `/scans/:id` | | `ScanJob` (`progress` while running, `summary` when completed) |
| GET | `/scans/:id/results` | | `LinkIssue[]` |
| POST | `/scans/:id/cancel` | | 204 |

`ScanStatus`: queued, running, completed, failed, cancelled. `IssueSeverity`: critical, warning, info. The frontend polls `GET /scans/:id` every 400 ms; swap for SSE/WebSocket inside `useScan.ts` later.
