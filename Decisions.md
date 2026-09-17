# Decisions
2026-09-17

1) I ship a single image whose entrypoint is the simjobs console script with subcommands (api, worker, migrate). The alternative would have been separate images per subcommand, but that would duplicate the dependency layer three times for no benefit at this size.

2) Exact Python pin, project requires-python = \"==3.12.*\" rather than >=3.12. Pinning it exactly means the resolution on my laptop and inside the image cannot land on different wheels. The cost is that a Python upgrade becomes a deliberate change, which I consider correct for a deployed service.

3) Hatchling over the uv build backend. uv init defaults to uv_build. I switched to hatchling because it is the most commonly used backend and it is independent of the tool I use to manage the environment. uv still does the resolving, installing and running.
