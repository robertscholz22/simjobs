"""Console entry point. Single binary with subcommands."""

from __future__ import annotations

import json

import typer

app = typer.Typer(add_completion=False, help="simjobs: reactor simulation job service")


@app.command()
def api(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Run the HTTP API."""
    import uvicorn

    uvicorn.run("simjobs.api:app", host=host, port=port)


@app.command()
def solve(param: list[str] = typer.Option([], "--param", "-p", help="k=v, repeatable")) -> None:
    """Run one simulation locally and print the scalar results."""
    from simjobs.solver import SimParams, run_simulation

    overrides = {}
    for item in param:
        key, _, value = item.partition("=")
        if not _:
            raise typer.BadParameter(f"expected k=v, got {item!r}")
        overrides[key] = value  # pydantic coerces the string to the field type

    result = run_simulation(SimParams(**overrides))
    print(json.dumps(result.model_dump(exclude={"series"}), indent=2))
