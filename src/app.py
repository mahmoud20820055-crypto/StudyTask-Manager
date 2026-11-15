"""StudyTask Manager - a small task tracker for university coursework.

Exposes a JSON REST API and a simple web UI. Data is stored in SQLite so the
service has no external dependencies and runs in a single container.
"""
import os
import sqlite3
from datetime import datetime, timezone

from flask import Flask, g, jsonify, render_template, request

DATABASE_PATH = os.environ.get("DATABASE_PATH", "/data/tasks.db")
VALID_PRIORITIES = ("low", "medium", "high")

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    title      TEXT    NOT NULL,
    course     TEXT    NOT NULL DEFAULT '',
    priority   TEXT    NOT NULL DEFAULT 'medium',
    due_date   TEXT,
    done       INTEGER NOT NULL DEFAULT 0,
    created_at TEXT    NOT NULL
);
"""


def create_app(database_path=None):
    app = Flask(__name__)
    app.config["DATABASE_PATH"] = database_path or DATABASE_PATH

    db_dir = os.path.dirname(app.config["DATABASE_PATH"])
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    def get_db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE_PATH"])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(_exc):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    with app.app_context():
        get_db().executescript(SCHEMA)
        get_db().commit()

    def row_to_task(row):
        task = dict(row)
        task["done"] = bool(task["done"])
        return task

    def validate(payload, partial=False):
        """Return (clean_fields, error_message)."""
        if not isinstance(payload, dict):
            return None, "Request body must be a JSON object."

        clean = {}
        if "title" in payload or not partial:
            title = str(payload.get("title", "")).strip()
            if not title:
                return None, "Field 'title' is required."
            if len(title) > 120:
                return None, "Field 'title' must be at most 120 characters."
            clean["title"] = title

        if "course" in payload:
            clean["course"] = str(payload["course"]).strip()[:60]

        if "priority" in payload:
            priority = str(payload["priority"]).lower()
            if priority not in VALID_PRIORITIES:
                return None, "Field 'priority' must be one of: low, medium, high."
            clean["priority"] = priority

        if "due_date" in payload:
            due = payload["due_date"]
            if due in (None, ""):
                clean["due_date"] = None
            else:
                try:
                    datetime.strptime(str(due), "%Y-%m-%d")
                except ValueError:
                    return None, "Field 'due_date' must use the format YYYY-MM-DD."
                clean["due_date"] = str(due)

        if "done" in payload:
            if not isinstance(payload["done"], bool):
                return None, "Field 'done' must be true or false."
            clean["done"] = int(payload["done"])

        return clean, None

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/health")
    def health():
        get_db().execute("SELECT 1")
        return jsonify(status="ok", service="studytask-manager")

    @app.get("/api/tasks")
    def list_tasks():
        query = "SELECT * FROM tasks"
        status = request.args.get("status")
        if status == "done":
            query += " WHERE done = 1"
        elif status == "pending":
            query += " WHERE done = 0"
        query += " ORDER BY done ASC, due_date IS NULL, due_date ASC, id DESC"
        rows = get_db().execute(query).fetchall()
        return jsonify([row_to_task(r) for r in rows])

    @app.post("/api/tasks")
    def create_task():
        clean, error = validate(request.get_json(silent=True))
        if error:
            return jsonify(error=error), 400
        db = get_db()
        cursor = db.execute(
            "INSERT INTO tasks (title, course, priority, due_date, done, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (
                clean["title"],
                clean.get("course", ""),
                clean.get("priority", "medium"),
                clean.get("due_date"),
                clean.get("done", 0),
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
            ),
        )
        db.commit()
        row = db.execute("SELECT * FROM tasks WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return jsonify(row_to_task(row)), 201

    @app.patch("/api/tasks/<int:task_id>")
    def update_task(task_id):
        clean, error = validate(request.get_json(silent=True), partial=True)
        if error:
            return jsonify(error=error), 400
        if not clean:
            return jsonify(error="No valid fields to update."), 400
        db = get_db()
        if db.execute("SELECT 1 FROM tasks WHERE id = ?", (task_id,)).fetchone() is None:
            return jsonify(error="Task not found."), 404
        assignments = ", ".join(f"{column} = ?" for column in clean)
        db.execute(f"UPDATE tasks SET {assignments} WHERE id = ?", (*clean.values(), task_id))
        db.commit()
        row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return jsonify(row_to_task(row))

    @app.delete("/api/tasks/<int:task_id>")
    def delete_task(task_id):
        db = get_db()
        cursor = db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        db.commit()
        if cursor.rowcount == 0:
            return jsonify(error="Task not found."), 404
        return "", 204

    @app.get("/api/stats")
    def stats():
        row = get_db().execute(
            "SELECT COUNT(*) AS total, COALESCE(SUM(done), 0) AS done FROM tasks"
        ).fetchone()
        return jsonify(total=row["total"], done=row["done"], pending=row["total"] - row["done"])

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
