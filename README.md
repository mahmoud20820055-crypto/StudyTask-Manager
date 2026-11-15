# StudyTask Manager

A small web application that helps university students keep track of their
coursework: assignments, lab reports and exams. Each task has a title, a
course, a priority and an optional due date, and can be marked as done.

The project ships as a single Docker image that contains a JSON REST API and a
simple web UI. Data is stored in SQLite inside a Docker volume, so tasks
survive container restarts.

## Tech stack

| Layer      | Technology                         |
|------------|------------------------------------|
| Language   | Python 3.12                        |
| Framework  | Flask 3                            |
| Server     | Gunicorn                           |
| Database   | SQLite (stored in a Docker volume) |
| Front end  | HTML, CSS, vanilla JavaScript      |
| Container  | Docker (multi-stage build), Docker Compose |
| CI         | GitHub Actions                     |

## Project structure

```
StudyTask-Manager/
├── src/                    # application source code
│   ├── app.py              # Flask app: API routes + database access
│   ├── wsgi.py             # gunicorn entry point
│   ├── templates/          # HTML page
│   └── static/             # CSS and JavaScript
├── tests/                  # pytest test suite
├── docs/
│   ├── screenshots/        # assignment screenshots
│   └── notes.md            # short technical notes
├── .github/workflows/      # CI pipeline
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── .dockerignore
├── .gitignore
└── README.md
```

## Requirements

Only [Docker](https://docs.docker.com/get-docker/) is required. You do not
need Python installed on your machine.

## Build and run with Docker

```bash
# 1. Clone the repository
git clone https://github.com/mahmoud20820055-crypto/StudyTask-Manager.git
cd StudyTask-Manager

# 2. Build the image
docker build -t studytask-manager .

# 3. Run the container
docker run -d --name studytask-manager -p 8000:8000 -v studytask-data:/data studytask-manager
```

Open <http://localhost:8000> in your browser.

### Using Docker Compose

```bash
docker compose up -d --build
```

### Using Make

```bash
make build   # build the image
make run     # start the container
make logs    # follow the logs
make test    # run the test suite inside a container
make stop    # stop and remove the container
```

## Stop and clean up

```bash
# Stop and remove the container
docker stop studytask-manager
docker rm studytask-manager

# Optional: remove the image and the stored data
docker rmi studytask-manager
docker volume rm studytask-data
```

With Compose: `docker compose down` (add `-v` to delete the data volume too).

## Configuration

| Variable        | Default          | Description                                   |
|-----------------|------------------|-----------------------------------------------|
| `PORT`          | `8000`           | Port the app listens on inside the container  |
| `DATABASE_PATH` | `/data/tasks.db` | Location of the SQLite database file          |
| `HOST_PORT`     | `8000`           | Host port used by `docker-compose.yml`        |

Example: run the app on host port 9000.

```bash
docker run -d --name studytask-manager -p 9000:8000 studytask-manager
```

## How to test it

**Web UI:** open <http://localhost:8000>, add a task, tick it as done, delete it.

**Health check:**

```bash
curl http://localhost:8000/health
# {"service":"studytask-manager","status":"ok"}
```

**API:**

```bash
# Create a task
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "OS Lab report", "course": "OS Lab", "priority": "high", "due_date": "2026-12-01"}'

# List tasks
curl http://localhost:8000/api/tasks

# Mark task 1 as done
curl -X PATCH http://localhost:8000/api/tasks/1 \
  -H "Content-Type: application/json" -d '{"done": true}'

# Statistics
curl http://localhost:8000/api/stats
```

### API reference

| Method | Endpoint              | Description                                      |
|--------|-----------------------|--------------------------------------------------|
| GET    | `/health`             | Service health status                            |
| GET    | `/api/tasks`          | List tasks (`?status=done` or `?status=pending`) |
| POST   | `/api/tasks`          | Create a task                                    |
| PATCH  | `/api/tasks/<id>`     | Update a task                                    |
| DELETE | `/api/tasks/<id>`     | Delete a task                                    |
| GET    | `/api/stats`          | Total / done / pending counters                  |

**Automated tests:** `make test`

## Screenshots

Screenshots of the build, the running container and the application are in
[`docs/screenshots/`](docs/screenshots/).

## Author

Mahmoud Basel Al-Juaidi (120230589) - OS Lab, Assignment #2.

This project was built from scratch for the assignment; it is not based on an
existing open-source project.
