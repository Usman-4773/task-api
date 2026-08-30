import os
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from supabase import create_client, Client

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in .env")

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

app = FastAPI(title="Auth Practice API")

security = HTTPBearer(auto_error=False)

REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(exist_ok=True)


# ============================================================
# MODELS
# ============================================================

class AuthRequest(BaseModel):
    email: str | None = None
    password: str | None = None


# ============================================================
# AUTHENTICATION
# ============================================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    if credentials is None:
        return JSONResponse(
            status_code=401,
            content={"error": "Access token required"}
        )

    token = credentials.credentials

    if not token:
        return JSONResponse(
            status_code=401,
            content={"error": "Access token required"}
        )

    try:
        response = supabase.auth.get_user(token)

        if not response.user:
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid or expired token"}
            )

        return response.user

    except Exception:
        return JSONResponse(
            status_code=401,
            content={"error": "Invalid or expired token"}
        )


# ============================================================
# BASIC ROUTES
# ============================================================

@app.get("/")
def root():
    return {
        "message": "Server running and connected to Supabase"
    }


@app.get("/public/info")
def public_info():
    return {
        "message": "Welcome stranger! This info is public."
    }


# ============================================================
# SIGNUP
# ============================================================

@app.post("/auth/signup", status_code=201)
def signup(data: AuthRequest):

    if not data.email or not data.password:
        return JSONResponse(
            status_code=400,
            content={
                "error": "Email and password are required"
            }
        )

    try:
        response = supabase.auth.sign_up({
            "email": data.email,
            "password": data.password
        })

        return {
            "user": (
                response.user.model_dump()
                if response.user
                else None
            )
        }

    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)}
        )


# ============================================================
# LOGIN
# ============================================================

@app.post("/auth/login")
def login(data: AuthRequest):

    if not data.email or not data.password:
        return JSONResponse(
            status_code=400,
            content={
                "error": "Email and password are required"
            }
        )

    try:
        response = supabase.auth.sign_in_with_password({
            "email": data.email,
            "password": data.password
        })

        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token
        }

    except Exception:
        return JSONResponse(
            status_code=401,
            content={
                "error": "Invalid login credentials"
            }
        )


# ============================================================
# PROTECTED PROFILE
# ============================================================

@app.get("/protected/profile")
def protected_profile(
    current_user=Depends(get_current_user)
):

    if isinstance(current_user, JSONResponse):
        return current_user

    return {
        "id": current_user.id,
        "email": current_user.email,
        "created_at": current_user.created_at
    }


# ============================================================
# PROTECTED DASHBOARD
# ============================================================

@app.get("/protected/dashboard")
def protected_dashboard(
    current_user=Depends(get_current_user)
):

    if isinstance(current_user, JSONResponse):
        return current_user

    return {
        "message": "Welcome to your protected dashboard!",
        "user_id": current_user.id,
        "email": current_user.email
    }


# ============================================================
# LOGOUT
# ============================================================

@app.post("/auth/logout", status_code=204)
def logout(
    current_user=Depends(get_current_user)
):

    if isinstance(current_user, JSONResponse):
        return current_user

    return None


# ============================================================
# PDF REPORT GENERATION
# ============================================================

def generate_pdf_report():

    # Query task data from Supabase
    response = supabase.table("tasks").select("*").execute()

    tasks = response.data or []

    # SQL-style aggregation of the queried data
    total_tasks = len(tasks)

    completed_tasks = sum(
        1
        for task in tasks
        if task.get("done") is True
    )

    pending_tasks = total_tasks - completed_tasks

    # Create unique PDF filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    filename = f"task_report_{timestamp}.pdf"

    file_path = REPORT_DIR / filename

    # Create PDF
    pdf = canvas.Canvas(
        str(file_path),
        pagesize=A4
    )

    width, height = A4

    # Title
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(
        60,
        height - 70,
        "Task Report"
    )

    # Date
    pdf.setFont("Helvetica", 10)
    pdf.drawString(
        60,
        height - 95,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    # Summary
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(
        60,
        height - 140,
        "Summary"
    )

    pdf.setFont("Helvetica", 12)

    pdf.drawString(
        80,
        height - 170,
        f"Total Tasks: {total_tasks}"
    )

    pdf.drawString(
        80,
        height - 195,
        f"Completed Tasks: {completed_tasks}"
    )

    pdf.drawString(
        80,
        height - 220,
        f"Pending Tasks: {pending_tasks}"
    )

    # Task list
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(
        60,
        height - 270,
        "Tasks"
    )

    y = height - 300

    pdf.setFont("Helvetica", 10)

    if not tasks:
        pdf.drawString(
            80,
            y,
            "No tasks found."
        )
    else:
        for task in tasks:

            task_id = task.get("id", "")
            title = task.get("title", "")
            done = task.get("done", False)

            status = "Completed" if done else "Pending"

            text = f"{task_id}. {title} - {status}"

            # Prevent extremely long lines
            if len(text) > 100:
                text = text[:97] + "..."

            pdf.drawString(
                80,
                y,
                text
            )

            y -= 20

            # New page if needed
            if y < 60:
                pdf.showPage()
                pdf.setFont("Helvetica", 10)
                y = height - 60

    pdf.save()

    print(f"PDF report generated: {file_path}")


# ============================================================
# CREATE REPORT - BACKGROUND JOB
# ============================================================

@app.post("/reports")
def create_report(
    background_tasks: BackgroundTasks
):

    background_tasks.add_task(
        generate_pdf_report
    )

    return {
        "message": "Report generation started",
        "status": "queued"
    }


# ============================================================
# LIST GENERATED REPORTS
# ============================================================

@app.get("/reports")
def list_reports():

    reports = [
        {
            "filename": path.name,
            "size_bytes": path.stat().st_size
        }
        for path in REPORT_DIR.glob("*.pdf")
    ]

    return {
        "reports": reports
    }


# ============================================================
# DOWNLOAD REPORT
# ============================================================

@app.get("/reports/{filename}")
def download_report(filename: str):

    # Prevent directory traversal
    safe_filename = Path(filename).name

    file_path = REPORT_DIR / safe_filename

    if not file_path.exists():
        return JSONResponse(
            status_code=404,
            content={
                "error": "Report not found"
            }
        )

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=safe_filename
    )