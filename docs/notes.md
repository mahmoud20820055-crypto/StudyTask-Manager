# Technical notes

## Environment

- Windows 11 with WSL2 (Ubuntu), Docker Engine 29 installed inside WSL
- Docker Compose v2 and Buildx plugins

## The biggest Docker problem I faced

**Problem:** `docker build` failed at the `pip install` step. The base image
`python:3.12-slim` was pulled without any issue, but inside the build
container every request to PyPI ended with:

```
Failed to establish a new connection: [Errno 101] Network is unreachable
ERROR: No matching distribution found for Flask==3.0.3
```

**Cause:** the problem was not in the Dockerfile. My WSL2 distribution had no
internet access in the default NAT mode, so I switched WSL to
`networkingMode=mirrored` in `.wslconfig`. After that the WSL host itself
could reach the internet (this is why the image pull worked, since the pull is
done by the Docker daemon on the host), but containers attached to Docker's
default bridge network still had no route to the outside.

**Solution:** build using the host network stack, so the build container uses
the same network as WSL:

```bash
docker build --network=host -t studytask-manager .
# or
make build NET=--network=host
```

After this the build finished in a few seconds. I added the `NET` variable to
the Makefile and a troubleshooting section to the README so that anyone with
the same setup can solve it quickly.

**What I learned from it:** an image pull and a `RUN` step use different
network paths. The pull is done by the daemon, while `RUN` executes inside a
container on the bridge network, so one can work while the other fails.

A second, smaller issue: the SQLite file must be writable by the non-root user
that runs the app. I solved it by creating `/data` and giving ownership to
`appuser` in the Dockerfile *before* declaring the volume, so the named volume
inherits the correct ownership.

## The most important Git/GitHub lesson

Small commits with a clear prefix (`feat:`, `docker:`, `docs:`, `fix:`) make
the history readable as a story of the project. When the Docker build broke,
it was easy to see that the Dockerfile commit was not the cause, because each
commit contained only one kind of change. I also learned to prepare
`.gitignore` before the first commit, so local files such as the database and
`__pycache__` never enter the history, and to use a feature branch with a
Pull Request instead of pushing everything directly to `main`.
