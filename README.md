# simjobs

A simulation job service. Submit the parameters of a small reactor simulation over HTTP, a worker
runs the solver, results land in Postgres.

# Quick start

```bash
uv sync
uv run simjobs solve
uv run simjops api
```

Then `curl localhost:8000/healthz`.
