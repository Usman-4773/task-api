from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI()

tasks = [
    {"id": 1, "title": "Learn FastAPI", "done": False},
    {"id": 2, "title": "Build CRUD API", "done": False},
    {"id": 3, "title": "Practice Git", "done": True}
]


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
    return tasks


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task

    return JSONResponse(
        status_code=404,
        content={"error": f"Task {task_id} not found"}
    )


@app.post("/tasks", status_code=201)
def create_task(task: TaskCreate):
    if task.title is None or not task.title.strip():
        return JSONResponse(
            status_code=400,
            content={"error": "Title is required and cannot be empty"}
        )

    new_id = max([task["id"] for task in tasks], default=0) + 1

    new_task = {
        "id": new_id,
        "title": task.title,
        "done": False
    }

    tasks.append(new_task)

    return new_task


@app.put("/tasks/{task_id}")
async def update_task(task_id: int, request: Request):
    for task in tasks:
        if task["id"] == task_id:
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

            if "title" in data:
                if not isinstance(data["title"], str) or not data["title"].strip():
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Title cannot be empty"}
                    )
                task["title"] = data["title"]

            if "done" in data:
                if not isinstance(data["done"], bool):
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Done must be true or false"}
                    )
                task["done"] = data["done"]

            if "title" not in data and "done" not in data:
                return JSONResponse(
                    status_code=400,
                    content={"error": "Provide title or done"}
                )

            return task

    return JSONResponse(
        status_code=404,
        content={"error": f"Task {task_id} not found"}
    )


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    for index, task in enumerate(tasks):
        if task["id"] == task_id:
            tasks.pop(index)
            return

    return JSONResponse(
        status_code=404,
        content={"error": f"Task {task_id} not found"}
    )