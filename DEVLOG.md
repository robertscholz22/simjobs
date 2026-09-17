# Devlog
2026-09-17
1) The solver, the CLI and a two-route API now run both on the host and inside a 511 MB image that starts as uid 10001 and reports healthy.
2) The surprise was how much of the Dockerfile is about cache boundaries rather than about what ends up in the image: splitting the dependency install from the source copy is the difference between a 20-second and a 2-second rebuild.
3) What I would tell a colleague: pin the base image by digest from day one, because retrofitting reproducibility after a build has started drifting is much harder than starting with it.
