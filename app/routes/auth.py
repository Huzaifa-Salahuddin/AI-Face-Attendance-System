from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.db import db
from datetime import datetime
import pytz
from typing import Optional
import asyncio
import hashlib  # Make sure to import hashlib

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
security = HTTPBearer()

# In-memory session storage
active_sessions = {}

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, msg: str = ""):
    return templates.TemplateResponse("login.html", {
        "request": request, 
        "msg": msg,
        "user_type": None  # No user logged in
    })

@router.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    # Hash the password
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    # First check admin users
    admin_user = await db.admin_users.find_one({"email": email, "password": hashed_password})
    
    if admin_user:
        # Create session for admin/user
        session_id = f"session_{admin_user['_id']}"
        active_sessions[session_id] = {
            "user_id": str(admin_user["_id"]),
            "email": admin_user["email"],
            "name": admin_user["name"],
            "type": admin_user["type"],
            "login_time": datetime.now()
        }
        
        # Set session in response based on user type
        if admin_user["type"] == "Admin":
            response = RedirectResponse(url="/admin", status_code=302)
        elif admin_user["type"] == "Employee":
            response = RedirectResponse(url="/employee-dashboard", status_code=302)
        else:  # User
            response = RedirectResponse(url="/user-dashboard", status_code=302)
        
        response.set_cookie(key="session_id", value=session_id, httponly=True)
        return response
    
    # If not an admin user, check regular employees
    employee = await db.users.find_one({"email": email, "password": hashed_password})
    
    if employee:
        # Create session for employee
        session_id = f"session_{employee['_id']}"
        active_sessions[session_id] = {
            "user_id": str(employee["_id"]),
            "email": employee["email"],
            "name": employee["name"],
            "type": "Employee",  # All regular users are employees
            "login_time": datetime.now()
        }
        
        response = RedirectResponse(url="/employee-dashboard", status_code=302)
        response.set_cookie(key="session_id", value=session_id, httponly=True)
        return response
    
    # If no user found, show error message
    return templates.TemplateResponse("login.html", {
        "request": request, 
        "msg": "Invalid credentials, Try again",
        "user_type": None
    })

@router.get("/logout")
async def logout(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id and session_id in active_sessions:
        del active_sessions[session_id]
    
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("session_id")
    return response

@router.get("/user-dashboard", response_class=HTMLResponse)
async def user_dashboard(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in active_sessions:
        return RedirectResponse(url="/login", status_code=302)
    
    user_session = active_sessions[session_id]
    if user_session["type"] != "User":
        return RedirectResponse(url="/admin", status_code=302)
    
    return templates.TemplateResponse("user_dashboard.html", {
        "request": request,
        "user": user_session,
        "user_type": user_session["type"]
    })

@router.get("/employee-dashboard", response_class=HTMLResponse)
async def employee_dashboard(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in active_sessions:
        return RedirectResponse(url="/login", status_code=302)
    
    user_session = active_sessions[session_id]
    if user_session["type"] != "Employee":
        if user_session["type"] == "Admin":
            return RedirectResponse(url="/admin", status_code=302)
        else:  # User
            return RedirectResponse(url="/user-dashboard", status_code=302)
    
    # Employee directly goes to attendance page
    return RedirectResponse(url="/attendance", status_code=302)

# Helper function to get user session
def get_user_session(request: Request):
    """Helper function to get user session"""
    session_id = request.cookies.get("session_id")
    if session_id and session_id in active_sessions:
        return active_sessions[session_id]
    return None

# Dependency to check if user is authenticated
def get_current_user(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in active_sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return active_sessions[session_id]

# Dependency to check if user is admin
def get_admin_user(request: Request):
    user = get_current_user(request)
    if user["type"] != "Admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

# Initialize default admin user
async def create_default_admin():
    existing_admin = await db.admin_users.find_one({"type": "Admin"})
    if not existing_admin:
        pakistan_time = datetime.now(pytz.timezone("Asia/Karachi"))
        default_admin = {
            "name": "Default Admin",
            "email": "admin@admin.com",
            "password": hashlib.sha256("admin123".encode()).hexdigest(),  # Hash the password
            "type": "Admin",
            "created_at": pakistan_time
        }
        await db.admin_users.insert_one(default_admin)
        print("✅ Default admin created: admin@admin.com / admin123")

# Initialize default employee user
async def create_default_employee():
    existing_employee = await db.admin_users.find_one({"type": "Employee"})
    if not existing_employee:
        pakistan_time = datetime.now(pytz.timezone("Asia/Karachi"))
        default_employee = {
            "name": "Default Employee",
            "email": "employee@test.com",
            "password": hashlib.sha256("emp123".encode()).hexdigest(),  # Hash the password
            "type": "Employee",
            "created_at": pakistan_time
        }
        await db.admin_users.insert_one(default_employee)
        print("✅ Default employee created: employee@test.com / emp123")