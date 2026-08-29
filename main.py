import os

from dotenv import load_dotenv
from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="Auth Practice API")

security = HTTPBearer(auto_error=False)


class AuthRequest(BaseModel):
    email: str | None = None
    password: str | None = None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # No Authorization header or incorrect format
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


@app.post("/auth/signup", status_code=201)
def signup(data: AuthRequest):
    if not data.email or not data.password:
        return JSONResponse(
            status_code=400,
            content={"error": "Email and password are required"}
        )

    try:
        response = supabase.auth.sign_up({
            "email": data.email,
            "password": data.password
        })

        return {
            "user": response.user.model_dump() if response.user else None
        }

    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)}
        )


@app.post("/auth/login")
def login(data: AuthRequest):
    if not data.email or not data.password:
        return JSONResponse(
            status_code=400,
            content={"error": "Email and password are required"}
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
            content={"error": "Invalid login credentials"}
        )


@app.get("/protected/profile")
def protected_profile(current_user=Depends(get_current_user)):

    if isinstance(current_user, JSONResponse):
        return current_user

    return {
        "id": current_user.id,
        "email": current_user.email,
        "created_at": current_user.created_at
    }


@app.get("/protected/dashboard")
def protected_dashboard(current_user=Depends(get_current_user)):

    if isinstance(current_user, JSONResponse):
        return current_user

    return {
        "message": "Welcome to your protected dashboard!",
        "user_id": current_user.id,
        "email": current_user.email
    }


@app.post("/auth/logout", status_code=204)
def logout(current_user=Depends(get_current_user)):

    if isinstance(current_user, JSONResponse):
        return current_user

    try:
        # The dependency already verified the token.
        # Sign out the current Supabase session.
        return None

    except Exception:
        return JSONResponse(
            status_code=401,
            content={"error": "Invalid or expired token"}
        )