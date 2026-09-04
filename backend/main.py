"""
FastAPI backend for the Revenue Recovery Agent dashboard.

Endpoints:
    POST /api/run?n=40   -> generates a fresh synthetic batch and runs the
                            full diagnose -> policy -> messenger -> audit
                            pipeline, returns the full result.
    GET  /api/last        -> returns the most recently run batch, if any.

Run with (from the project root, not inside backend/):
    uvicorn backend.main:app --reload --port 8000
"""
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from data.generate_data import make_checkout
from agent.orchestrator import run_batch

app = FastAPI(title="Revenue Recovery Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_last_result = {"rows": [], "stats": {}}


def _serialize(trail, stats):
    return {"rows": trail.rows, "stats": stats}


@app.post("/api/run")
def run(n: int = Query(default=40, ge=5, le=200)):
    checkouts = [make_checkout(i) for i in range(n)]
    trail, stats = run_batch(checkouts)
    result = _serialize(trail, stats)
    global _last_result
    _last_result = result
    return result


@app.get("/api/last")
def last():
    return _last_result


@app.get("/api/health")
def health():
    return {"status": "ok"}
