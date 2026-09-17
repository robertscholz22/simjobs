"""HTTP API. Runs the solver in-process. Later to be enhanced with a job queue."""

from __future__ import annotations

from fastapi import FastAPI

from simjobs.solver import SimParams, SimResult, run_simulation

app = FastAPI(title="simjobs")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Liveness. Most not touch any dependency."""
    return {"status": "ok"}


@app.post("/solve")
def solve(params: SimParams) -> SimResult:
    """Synchronous solve. Blocks the worker thread."""
    # TODO: Job queue
    return run_simulation(params)
