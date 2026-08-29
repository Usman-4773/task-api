import os

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from supabase import create_client, Client


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL must be set in .env")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in .env")


# ============================================================
# SUPABASE
# ============================================================

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="Task API - Auth Practice",
    version="2.0"
)


# ============================================================
# AUTHENTICATION
# ============================================================

security = HTTPBearer(auto_error=False)


class AuthRequest(BaseModel):
    email: str
    password: str


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Reusable authentication dependency.

    Requires:
    Authorization: Bearer <access_token>
    """

    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail={"error": "Access token required"}
        )

    token = credentials.credentials

    if not token:
        raise HTTPException(
            status_code=401,
            detail={"error": "Access token required"}
        )

    try:
        response = supabase.auth.get_user(token)

        if response.user is None:
            raise HTTPException(
                status_code=401,
                detail={"error": "Invalid or expired token"}
            )

        return response.user

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=401,
            detail={"error": "Invalid or expired token"}
        )


# ============================================================
# AUTH ROUTES
# ============================================================

@app.post("/auth/signup", status_code=201)
def signup(data: AuthRequest):

    if not data.email.strip() or not data.password.strip():
        return JSONResponse(
            status_code=400,
            content={"error": "Email and password are required"}
        )

    try:
        response = supabase.auth.sign_up(
            {
                "email": data.email,
                "password": data.password
            }
        )

        return {
            "user": response.user.model_dump()
            if response.user
            else None
        }

    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)}
        )


@app.post("/auth/login")
def login(data: AuthRequest):

    if not data.email.strip() or not data.password.strip():
        return JSONResponse(
            status_code=400,
            content={"error": "Email and password are required"}
        )

    try:
        response = supabase.auth.sign_in_with_password(
            {
                "email": data.email,
                "password": data.password
            }
        )

        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token
        }

    except Exception:
        return JSONResponse(
            status_code=401,
            content={"error": "Invalid login credentials"}
        )


@app.post("/auth/logout", status_code=204)
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):

    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail={"error": "Access token required"}
        )

    token = credentials.credentials

    try:
        supabase.auth.sign_out()

        return

    except Exception:
        raise HTTPException(
            status_code=401,
            detail={"error": "Invalid or expired token"}
        )


# ============================================================
# PUBLIC ROUTE
# ============================================================

@app.get("/public/info")
def public_info():

    return {
        "message": "Welcome stranger! This info is public."
    }


# ============================================================
# PROTECTED ROUTES
# ============================================================

@app.get("/protected/profile")
def protected_profile(user=Depends(get_current_user)):

    return {
        "id": user.id,
        "email": user.email,
        "created_at": user.created_at
    }


@app.get("/protected/dashboard")
def protected_dashboard(user=Depends(get_current_user)):

    return {
        "message": "Welcome to your protected dashboard!",
        "user_id": user.id,
        "email": user.email
    }


# ============================================================
# DATABASE / TASK REPOSITORY
# ============================================================

class TaskRepository:

    def get_connection(self):
        return psycopg2.connect(DATABASE_URL)

    def get_all(self):
        connection = self.get_connection()
        cursor = connection.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            "SELECT id, title, done FROM tasks ORDER BY id"
        )

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


# ============================================================
# ORIGINAL API ROUTES
# ============================================================

@app.get("/")
def home():

    return {
        "name": "Task API",
        "version": "2.0",
        "endpoints": [
            "/tasks",
            "/auth/signup",
            "/auth/login",
            "/auth/logout",
            "/public/info",
            "/protected/profile",
            "/protected/dashboard"
        ]
    }


@app.get("/health")
def health():

    return {
        "status": "ok"
    }


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
            content={
                "error": f"Task {task_id} not found"
            }
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
            content={
                "error": "Title is required and cannot be empty"
            }
        )

    task_id = repository.create(task.title)

    return {
        "id": task_id,
        "title": task.title,
        "done": False
    }


@app.put("/tasks/{task_id}")
async def update_task(
    task_id: int,
    request: Request
):

    existing_task = repository.get(task_id)

    if existing_task is None:

        return JSONResponse(
            status_code=404,
            content={
                "error": f"Task {task_id} not found"
            }
        )

    try:
        data = await request.json()

    except Exception:

        return JSONResponse(
            status_code=400,
            content={
                "error": "Invalid JSON body"
            }
        )

    if not isinstance(data, dict) or not data:

        return JSONResponse(
            status_code=400,
            content={
                "error": "Update body cannot be empty"
            }
        )

    title = existing_task["title"]
    done = bool(existing_task["done"])

    if "title" in data:

        if (
            not isinstance(data["title"], str)
            or not data["title"].strip()
        ):

            return JSONResponse(
                status_code=400,
                content={
                    "error": "Title cannot be empty"
                }
            )

        title = data["title"]

    if "done" in data:

        if not isinstance(data["done"], bool):

            return JSONResponse(
                status_code=400,
                content={
                    "error": "Done must be true or false"
                }
            )

        done = data["done"]

    if "title" not in data and "done" not in data:

        return JSONResponse(
            status_code=400,
            content={
                "error": "Provide title or done"
            }
        )

    repository.update(
        task_id,
        title,
        done
    )

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
            content={
                "error": f"Task {task_id} not found"
            }
        )

    repository.delete(task_id)

    return