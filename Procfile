# =============================================================================
# IndoGovRAG - Procfile for Render / Railway / other PaaS
# =============================================================================
# Usage:
#   Render:    Set "Start Command" to: web: make run-production
#   Railway:   Set "Start Command" to: web: uvicorn api.main:app --host 0.0.0.0 --port $PORT
#   Heroku:    git push heroku main
# =============================================================================

# FastAPI web server (primary service)
web: uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}

# Alternative with worker for background tasks (APScheduler)
# worker: python -m apscheduler.executors.pool --max_workers=2