# Deployment Guide (Render + Vercel)

This project deploys as two separate services:

- **Backend** (FastAPI) → [Render](https://render.com), as a Docker web service.
- **Frontend** (Next.js) → [Vercel](https://vercel.com).

They're independent deployments talking over HTTPS - CORS on the backend already
allows all origins (`app/main.py`), so no extra config is needed there.

---

## 1. Backend on Render

The repo root has a `render.yaml` blueprint that builds `Dockerfile` and exposes
`/health` as the health check.

### Deploy via Blueprint (recommended)

1. Push this repo to GitHub (if not already there).
2. In the Render dashboard: **New → Blueprint**, pick this repo. Render reads
   `render.yaml` and creates the `college-chatbot-backend` web service.
3. `render.yaml` lists env vars with `sync: false` for anything secret - Render
   will prompt you to fill these in during blueprint setup (or afterwards under
   **Environment**):
   - `GEMINI_API_KEY`
   - `METABASE_URL`
   - `METABASE_USERNAME`
   - `METABASE_PASSWORD`
   All other env vars (LLM provider, rate limits, etc.) are already set from
   `render.yaml` and match what's in `.env.example`.
4. Deploy. Render builds the Docker image and starts the container listening on
   the `$PORT` it assigns (the Dockerfile's `CMD` already respects `$PORT`, see
   below).
5. Once live, note the backend URL Render gives you, e.g.
   `https://college-chatbot-backend.onrender.com`. Confirm it works:
   ```bash
   curl https://college-chatbot-backend.onrender.com/health
   ```

### Deploy manually (without the blueprint)

If you'd rather click through the UI instead of using the blueprint:

1. **New → Web Service**, connect the repo, runtime **Docker**, root directory `.`
   (Dockerfile at repo root).
2. Health check path: `/health`.
3. Add the same env vars listed in `render.yaml` under **Environment**.

### Notes

- The `Dockerfile` CMD was changed to
  `uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}` so it binds
  to whatever port Render assigns (`$PORT`), while still defaulting to `8000`
  for local `docker-compose` use.
- Render's free plan spins the service down after inactivity - the first
  request after idle will be slow (cold start, includes the LLM warmup call in
  `app/main.py`'s lifespan). Upgrade the plan if you need to avoid that.
- `DATABASE_URL` is set to the sqlite fallback, but since `USE_METABASE=true`,
  the backend actually queries through Metabase - `DATABASE_URL`/sqlite is
  unused in that mode (kept only so `Settings` has a valid default).

---

## 2. Frontend on Vercel

1. In the Vercel dashboard: **Add New → Project**, import this repo.
2. Set **Root Directory** to `frontend` (this is a monorepo - the Next.js app
   lives in `frontend/`, not the repo root). Vercel auto-detects the Next.js
   framework preset once you do.
3. Add these Environment Variables (Project Settings → Environment Variables),
   both pointing at your Render backend URL from step 1 (see
   `frontend/.env.example`):
   - `NEXT_PUBLIC_BACKEND_URL` = `https://college-chatbot-backend.onrender.com`
   - `NEXT_PUBLIC_API_URL` = `https://college-chatbot-backend.onrender.com`

   Both are needed: the chat request calls the backend directly via
   `NEXT_PUBLIC_BACKEND_URL` (to avoid proxy timeouts on long LLM calls, see
   `frontend/src/lib/api.ts`), while the conversations/logs endpoints go
   through the Next.js rewrite proxy configured via `NEXT_PUBLIC_API_URL` in
   `next.config.js`.
4. Deploy. Vercel builds and hosts the app directly (the `output: 'standalone'`
   Docker-only setting in `next.config.js` is skipped automatically on Vercel -
   it only activates when `DOCKER_BUILD=true`, which only `Dockerfile.frontend`
   sets).

### Verify

```bash
curl -X POST https://your-app.vercel.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "How many students are there?"}'
```

Should return a JSON answer generated via the Render backend.

---

## Local Docker Compose (unaffected)

`docker-compose.yml` still runs both services together locally exactly as
before - the Render/Vercel changes are additive (env-var gated) and don't
change local behavior.
