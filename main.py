from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")


class TaskRepository:
    def get_connection(self):
        return psycopg2.connect(DATABASE_URL)

    def get_all(self):
        connection = self.get_connection()
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT id, title, done FROM tasks ORDER BY id")
        rows = cursor.fetchall()
        cursor.close()
        connection.close()
        return rows

    def get(self, task_id):
        connection = self.get_connection()
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            "SELECT id, title, done FROM tasks WHERE id = %s",
            (task_id,)
        )
        row = cursor.fetchone()
        cursor.close()
        connection.close()
        return row

    def create(self, title):
        connection = self.get_connection()
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING id",
            (title, False)
        )
        task_id = cursor.fetchone()["id"]
        connection.commit()
        cursor.close()
        connection.close()
        return task_id

    def update(self, task_id, title, done):
        connection = self.get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE tasks SET title = %s, done = %s WHERE id = %s",
            (title, done, task_id)
        )
        connection.commit()
        cursor.close()
        connection.close()

    def delete(self, task_id):
        connection = self.get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "DELETE FROM tasks WHERE id = %s",
            (task_id,)
        )
        connection.commit()
        cursor.close()
        connection.close()


repository = TaskRepository()


class TaskCreate(BaseModel):
    title: str | None = None


@app.get("/")
def home():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tasks")
def get_tasks():
    rows = repository.get_all()

    return [
        {
            "id": row["id"],
            "title": row["title"],
            "done": bool(row["done"])
        }
        for row in rows
    ]


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    row = repository.get(task_id)

    if row is None:
        return JSONResponse(
            status_code=404,
            content={"error": f"Task {task_id} not found"}
        )

    return {
        "id": row["id"],
        "title": row["title"],
        "done": bool(row["done"])
    }


@app.post("/tasks", status_code=201)
def create_task(task: TaskCreate):
    if task.title is None or not task.title.strip():
        return JSONResponse(
            status_code=400,
            content={"error": "Title is required and cannot be empty"}
        )

    task_id = repository.create(task.title)

    return {
        "id": task_id,
        "title": task.title,
        "done": False
    }


@app.put("/tasks/{task_id}")
async def update_task(task_id: int, request: Request):
    existing_task = repository.get(task_id)

    if existing_task is None:
        return JSONResponse(
            status_code=404,
            content={"error": f"Task {task_id} not found"}
        )

    try:
        data = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid JSON body"}
        )

    if not isinstance(data, dict) or not data:
        return JSONResponse(
            status_code=400,
            content={"error": "Update body cannot be empty"}
        )

    title = existing_task["title"]
    done = bool(existing_task["done"])

    if "title" in data:
        if not isinstance(data["title"], str) or not data["title"].strip():
            return JSONResponse(
                status_code=400,
                content={"error": "Title cannot be empty"}
            )
        title = data["title"]

    if "done" in data:
        if not isinstance(data["done"], bool):
            return JSONResponse(
                status_code=400,
                content={"error": "Done must be true or false"}
            )
        done = data["done"]

    if "title" not in data and "done" not in data:
        return JSONResponse(
            status_code=400,
            content={"error": "Provide title or done"}
        )

    repository.update(task_id, title, done)

    return {
        "id": task_id,
        "title": title,
        "done": done
    }


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    existing_task = repository.get(task_id)

    if existing_task is None:
        return JSONResponse(
            status_code=404,
            content={"error": f"Task {task_id} not found"}
        )

    repository.delete(task_id)

    return