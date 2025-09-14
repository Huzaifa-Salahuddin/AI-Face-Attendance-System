from dotenv import load_dotenv
load_dotenv() 
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager

# Import routes and services
from app.routes.auth import router as auth_router, create_default_admin, create_default_employee, active_sessions, get_user_session
from app.routes.admin import router as admin_router
from app.routes.attendance import router as attendance_router
from app.services.db import client


# --- Authentication dependencies ---
def require_auth(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in active_sessions:
        raise HTTPException(status_code=401, detail="Authentication required")
    return active_sessions[session_id]

def require_admin(request: Request):
    user = require_auth(request)
    if user["type"] != "Admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# --- Lifespan context manager ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Attendance System...")

    try:
        await client.admin.command("ping")
        print("✅ Database connection successful")

        # Run startup tasks
        print("⚡ Running startup tasks...")
        await create_default_admin()
        await create_default_employee()
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

    yield

    # Shutdown
    print("🔴 Shutting down Attendance System...")
    client.close()


# --- Create FastAPI app ---
app = FastAPI(
    title="Face Recognition Attendance System",
    description="A modern attendance system using face recognition technology",
    version="1.0.0",
    lifespan=lifespan
)

# --- Include routers ---
app.include_router(auth_router)
app.include_router(admin_router, prefix="", tags=["admin"])
app.include_router(attendance_router, prefix="", tags=["attendance"])


# --- Routes ---
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    # Use the helper function instead of direct access
    user_session = get_user_session(request)
    if not user_session:
        return RedirectResponse(url="/login", status_code=302)

    if user_session["type"] == "Admin":
        return RedirectResponse(url="/admin", status_code=302)
    elif user_session["type"] == "Employee":
        return RedirectResponse(url="/attendance", status_code=302)
    else:
        return RedirectResponse(url="/user-dashboard", status_code=302)


# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Static files & templates ---
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


# --- Health check ---
@app.get("/health")
async def health_check():
    try:
        await client.admin.command("ping")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}


# --- API Info ---
@app.get("/api/info")
async def api_info():
    return {
        "app_name": "Face Recognition Attendance System",
        "version": "1.0.0",
        "description": "Modern attendance tracking using facial recognition",
        "endpoints": {
            "admin_dashboard": "/admin",
            "register_employee": "/admin/register",
            "mark_attendance": "/attendance",
            "attendance_records": "/admin/attendance-records",
            "export_data": "/admin/export",
        },
    }


# --- Error handlers ---
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return templates.TemplateResponse(
        "404.html", {"request": request, "error": "Page not found"}, status_code=404
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    return templates.TemplateResponse(
        "500.html", {"request": request, "error": "Internal server error"}, status_code=500
    )


# --- Run the app ---
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # ⚠️ disable in production
        log_level="info",
    )