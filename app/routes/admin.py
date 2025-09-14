from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from app.services.db import db
from app.services.face_service import quick_face_verify as verify_faces
from datetime import datetime, timezone, timedelta
from bson import ObjectId
import pytz
import csv
import io
from app.routes.auth import active_sessions
from bson import ObjectId

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def get_user_session(request: Request):
    """Helper function to get user session and type"""
    session_id = request.cookies.get("session_id")
    if session_id and session_id in active_sessions:
        return active_sessions[session_id]
    return None

@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    # Check authentication
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in active_sessions:
        return RedirectResponse(url="/login", status_code=302)
    
    user_session = active_sessions[session_id]
    if user_session["type"] != "Admin":
        return RedirectResponse(url="/user-dashboard", status_code=302)
    
    users = await db.users.find().to_list(100)
    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request, 
        "users": users,
        "user_type": user_session["type"]
    })

@router.get("/admin/register", response_class=HTMLResponse)
async def register_page(request: Request):
    # Check authentication
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in active_sessions:
        return RedirectResponse(url="/login", status_code=302)
    
    user_session = active_sessions[session_id]
    # Both Admin and User can access this page
    
    return templates.TemplateResponse("register_employee.html", {
        "request": request,
        "user_type": user_session["type"]
    })

@router.post("/admin/register")
async def register_employee(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    image: UploadFile = File(...)
):
    # Check authentication
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in active_sessions:
        return RedirectResponse(url="/login", status_code=302)
    
    user_session = active_sessions[session_id]
    
    try:
        # Check if email already exists
        existing_user = await db.users.find_one({"email": email})
        if existing_user:
            # Return JSON error response instead of redirect for AJAX handling
            return {"status": "error", "message": "Email already registered."}

        # Read and validate image
        image_data = await image.read()
        if not image_data or len(image_data) < 1000:
            return {"status": "error", "message": "Invalid or empty image. Please upload a valid image file."}

        # Validate image type (optional but recommended)
        if not image.content_type or not image.content_type.startswith('image/'):
            return {"status": "error", "message": "Please upload a valid image file."}

        pakistan_time = datetime.now(pytz.timezone("Asia/Karachi"))

        user = {
            "name": name.strip(),  # Remove extra whitespace
            "email": email.strip().lower(),  # Normalize email
            "face_image": image_data,
            "created_at": pakistan_time
        }

        # Insert the user into database
        result = await db.users.insert_one(user)
        
        # Verify the insertion was successful
        if result.inserted_id:
            print(f"✅ Employee {name} registered successfully with ID: {result.inserted_id}")
            
            # Return success response for both Admin and User
            return {
                "status": "success", 
                "message": f"Employee {name} registered successfully!",
                "redirect_url": "/admin" if user_session["type"] == "Admin" else "/user-dashboard"
            }
        else:
            return {"status": "error", "message": "Failed to register employee. Please try again."}
            
    except Exception as e:
        print(f"❌ Error registering employee: {str(e)}")
        return {"status": "error", "message": f"Registration failed: {str(e)}"}

@router.get("/admin/update/{user_id}", response_class=HTMLResponse)
async def update_employee_page(user_id: str, request: Request):
    # Check authentication - only Admin can update
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in active_sessions:
        return RedirectResponse(url="/login", status_code=302)
    
    user_session = active_sessions[session_id]
    if user_session["type"] != "Admin":
        return RedirectResponse(url="/user-dashboard", status_code=302)
    
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return RedirectResponse(url="/admin", status_code=302)
    
    return templates.TemplateResponse("update_employee.html", {
        "request": request, 
        "user": user,
        "user_type": user_session["type"]
    })

@router.post("/admin/update/{user_id}")
async def update_employee(user_id: str, request: Request, name: str = Form(...), email: str = Form(...)):
    # Check authentication - only Admin can update
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in active_sessions:
        return RedirectResponse(url="/login", status_code=302)
    
    user_session = active_sessions[session_id]
    if user_session["type"] != "Admin":
        return RedirectResponse(url="/user-dashboard", status_code=302)
    
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"name": name, "email": email}}
    )
    return RedirectResponse("/admin", status_code=302)

@router.get("/admin/delete/{user_id}")
async def delete_employee(user_id: str, request: Request):
    # Check authentication - only Admin can delete
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in active_sessions:
        return RedirectResponse(url="/login", status_code=302)
    
    user_session = active_sessions[session_id]
    if user_session["type"] != "Admin":
        return RedirectResponse(url="/user-dashboard", status_code=302)
    
    await db.users.delete_one({"_id": ObjectId(user_id)})
    return RedirectResponse("/admin", status_code=302)

@router.get("/admin/export")
async def export_csv(request: Request):
    # Check authentication - only Admin can export
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in active_sessions:
        return RedirectResponse(url="/login", status_code=302)
    
    user_session = active_sessions[session_id]
    if user_session["type"] != "Admin":
        return RedirectResponse(url="/user-dashboard", status_code=302)
    
    users = await db.users.find().to_list(100)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Email", "Created At"])
    for user in users:
        created_at = user.get("created_at", datetime.utcnow())
        pk_tz = pytz.timezone("Asia/Karachi")
        created_at = created_at.astimezone(pk_tz)
        writer.writerow([user["name"], user["email"], created_at.strftime("%Y-%m-%d %H:%M:%S")])
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=employees.csv"}
    )

@router.get("/admin/attendance-records", response_class=HTMLResponse)
async def attendance_records(request: Request):
    # Check authentication - only Admin can view records
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in active_sessions:
        return RedirectResponse(url="/login", status_code=302)
    
    user_session = active_sessions[session_id]
    if user_session["type"] != "Admin":
        return RedirectResponse(url="/user-dashboard", status_code=302)
    
    raw_records = await db.attendance.find().sort("date", -1).to_list(500)
    pk_tz = pytz.timezone("Asia/Karachi")

    records = []
    for r in raw_records:
        date = r.get("date", "-")
        checkin = r.get("checkin") or r.get("check_in")
        checkout = r.get("checkout") or r.get("check_out")
        late = r.get("late", False)

        def format_time(t):
            if not t or t == "":
                return None
            if isinstance(t, str):
                return t  # already formatted string
            try:
                return t.strftime("%H:%M:%S")
            except Exception:
                return None

        records.append({
            "name": r.get("name", "-"),
            "email": r.get("email", "-"),
            "date": date,
            "checkin": format_time(checkin),
            "checkout": format_time(checkout),
            "late": late
        })

    return templates.TemplateResponse("attendance_records.html", {
        "request": request,
        "records": records,
        "user_type": user_session["type"]
    })

# All the delete functions - only for Admin
@router.post("/admin/delete-all")
async def delete_all_records(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in active_sessions:
        return RedirectResponse(url="/login", status_code=302)
    
    user_session = active_sessions[session_id]
    if user_session["type"] != "Admin":
        return RedirectResponse(url="/user-dashboard", status_code=302)
    
    await db.attendance.delete_many({})
    return RedirectResponse(url="/admin/attendance-records", status_code=303)

@router.post("/admin/delete-by-date")
async def delete_by_date(request: Request, date: str = Form(...)):
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in active_sessions:
        return RedirectResponse(url="/login", status_code=302)
    
    user_session = active_sessions[session_id]
    if user_session["type"] != "Admin":
        return RedirectResponse(url="/user-dashboard", status_code=302)
    
    await db.attendance.delete_many({
        "date": date  # Match directly with the string format you stored
    })
    return RedirectResponse(url="/admin/attendance-records", status_code=303)

@router.post("/admin/delete-by-name")
async def delete_by_name(request: Request, name: str = Form(...)):
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in active_sessions:
        return RedirectResponse(url="/login", status_code=302)
    
    user_session = active_sessions[session_id]
    if user_session["type"] != "Admin":
        return RedirectResponse(url="/user-dashboard", status_code=302)
    
    await db.attendance.delete_many({"name": name})
    return RedirectResponse(url="/admin/attendance-records", status_code=303)

@router.post("/admin/delete-selected-employees")
async def delete_selected_employees(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in active_sessions:
        return RedirectResponse(url="/login", status_code=302)
    
    user_session = active_sessions[session_id]
    if user_session["type"] != "Admin":
        return RedirectResponse(url="/user-dashboard", status_code=302)
    
    form = await request.form()
    ids = form.getlist("user_ids")
    for uid in ids:
        await db.users.delete_one({"_id": ObjectId(uid)})
    return RedirectResponse(url="/admin", status_code=302)

# Handle Users and Admin routes - Only for Admin
@router.get("/admin/handle-users", response_class=HTMLResponse)
async def handle_users(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in active_sessions:
        return RedirectResponse(url="/login", status_code=302)
    
    user_session = active_sessions[session_id]
    if user_session["type"] != "Admin":
        return RedirectResponse(url="/user-dashboard", status_code=302)
    
    # Get all admin users
    admin_users = await db.admin_users.find().to_list(100)
    
    # Mark default admin
    for user in admin_users:
        user["is_default"] = user.get("email") == "admin@admin.com"
    
    return templates.TemplateResponse("handle_users.html", {
        "request": request,
        "admin_users": admin_users,
        "user_type": user_session["type"]
    })

@router.get("/admin/add-user", response_class=HTMLResponse)
async def add_user_page(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in active_sessions:
        return RedirectResponse(url="/login", status_code=302)
    
    user_session = active_sessions[session_id]
    if user_session["type"] != "Admin":
        return RedirectResponse(url="/user-dashboard", status_code=302)
    
    return templates.TemplateResponse("add_user.html", {
        "request": request,
        "user_type": user_session["type"]
    })

@router.post("/admin/add-user")
async def add_user(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    user_type: str = Form(...)
):
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in active_sessions:
        return RedirectResponse(url="/login", status_code=302)
    
    user_session = active_sessions[session_id]
    if user_session["type"] != "Admin":
        return RedirectResponse(url="/user-dashboard", status_code=302)
    
    # Check if email already exists
    existing_user = await db.admin_users.find_one({"email": email})
    if existing_user:
        return templates.TemplateResponse("add_user.html", {
            "request": request,
            "error": "Email already exists",
            "user_type": user_session["type"]
        })
    
    # Create new user
    pakistan_time = datetime.now(pytz.timezone("Asia/Karachi"))
    new_user = {
        "name": name,
        "email": email,
        "password": password,
        "type": user_type,
        "created_at": pakistan_time
    }
    
    await db.admin_users.insert_one(new_user)
    return RedirectResponse(url="/admin/handle-users", status_code=302)

import hashlib  # Add this import for password hashing

@router.get("/admin/update-user/{user_id}", response_class=HTMLResponse)
async def render_update_form(user_id: str, request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in active_sessions:
        return RedirectResponse(url="/login", status_code=302)
        
    user_session = active_sessions[session_id]
    if user_session["type"] != "Admin":
        return RedirectResponse(url="/user-dashboard", status_code=302)
    
    # Validate ObjectId format
    try:
        user = await db.admin_users.find_one({"_id": ObjectId(user_id)})
    except Exception as e:
        return HTMLResponse("Invalid user ID format", status_code=400)
    
    if not user:
        return HTMLResponse("User not found", status_code=404)

    # Get any message from query parameters (for success/error messages)
    msg = request.query_params.get("msg", "")
    msg_type = request.query_params.get("msg_type", "info")
    
    return templates.TemplateResponse("update_user.html", {
        "request": request, 
        "user": user,
        "msg": msg,
        "msg_type": msg_type
    })

@router.post("/admin/update-user/{user_id}")
async def update_user(
    user_id: str,
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    type: str = Form(...)
):
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in active_sessions:
        return RedirectResponse(url="/login", status_code=302)
        
    user_session = active_sessions[session_id]
    if user_session["type"] != "Admin":
        return RedirectResponse(url="/user-dashboard", status_code=302)

    try:
        # Validate ObjectId format
        obj_id = ObjectId(user_id)
        
        # Check if user exists
        existing_user = await db.admin_users.find_one({"_id": obj_id})
        if not existing_user:
            return RedirectResponse(
                url=f"/admin/update-user/{user_id}?msg=User not found&msg_type=error", 
                status_code=302
            )
        
        # Check for email uniqueness (if email is being changed)
        if existing_user["email"] != email:
            email_exists = await db.admin_users.find_one({"email": email, "_id": {"$ne": obj_id}})
            if email_exists:
                return RedirectResponse(
                    url=f"/admin/update-user/{user_id}?msg=Email already exists&msg_type=error", 
                    status_code=302
                )
        
        # Hash password if it's different from stored one
        hashed_password = password
        if password != existing_user["password"]:  # If password is being changed
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # Update user
        result = await db.admin_users.update_one(
            {"_id": obj_id},
            {"$set": {
                "name": name.strip(),
                "email": email.strip().lower(),
                "password": hashed_password,
                "type": type
            }}
        )
        
        if result.modified_count > 0:
            return RedirectResponse(
                url=f"/admin/update-user/{user_id}?msg=User updated successfully!&msg_type=success", 
                status_code=302
            )
        else:
            return RedirectResponse(
                url=f"/admin/update-user/{user_id}?msg=No changes were made&msg_type=warning", 
                status_code=302
            )
            
    except Exception as e:
        print(f"Error updating user: {e}")  # Log the error
        return RedirectResponse(
            url=f"/admin/update-user/{user_id}?msg=Error updating user. Please try again.&msg_type=error", 
            status_code=302
        )
    
@router.get("/admin/delete-user/{user_id}")
async def delete_user(user_id: str, request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in active_sessions:
        return RedirectResponse(url="/login", status_code=302)
        
    user_session = active_sessions[session_id]
    if user_session["type"] != "Admin":
        return RedirectResponse(url="/user-dashboard", status_code=302)

    try:
        # Check if it's the default admin
        user = await db.admin_users.find_one({"_id": ObjectId(user_id)})
        if user and user.get("email") == "admin@admin.com":
            return RedirectResponse(
                url="/admin/handle-users?msg=Cannot delete default admin&msg_type=warning", 
                status_code=302
            )
        
        if not user:
            return RedirectResponse(
                url="/admin/handle-users?msg=User not found&msg_type=error", 
                status_code=302
            )

        await db.admin_users.delete_one({"_id": ObjectId(user_id)})
        return RedirectResponse(
            url="/admin/handle-users?msg=User deleted successfully&msg_type=success", 
            status_code=302
        )
        
    except Exception as e:
        print(f"Error deleting user: {e}")
        return RedirectResponse(
            url="/admin/handle-users?msg=Error deleting user&msg_type=error", 
            status_code=302
        )

@router.get("/admin/make-admin/{user_id}")
async def make_admin(user_id: str, request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in active_sessions:
        return RedirectResponse(url="/login", status_code=302)
    
    user_session = active_sessions[session_id]
    if user_session["type"] != "Admin":
        return RedirectResponse(url="/user-dashboard", status_code=302)
    
    await db.admin_users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"type": "Admin"}}
    )
    return RedirectResponse(url="/admin/handle-users", status_code=302)

@router.get("/admin/make-user/{user_id}")
async def make_user(user_id: str, request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in active_sessions:
        return RedirectResponse(url="/login", status_code=302)
    
    user_session = active_sessions[session_id]
    if user_session["type"] != "Admin":
        return RedirectResponse(url="/user-dashboard", status_code=302)
    
    await db.admin_users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"type": "User"}}
    )
    return RedirectResponse(url="/admin/handle-users", status_code=302)


@router.post("/admin/delete-selected-records")
async def delete_selected_records(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in active_sessions:
        return RedirectResponse(url="/login", status_code=302)
    
    user_session = active_sessions[session_id]
    if user_session["type"] != "Admin":
        return RedirectResponse(url="/user-dashboard", status_code=302)
    
    data = await request.json()
    records = data.get('records', [])
    
    for record in records:
        await db.attendance.delete_many({
            "name": record['name'],
            "date": record['date']
        })
    
    return {"status": "success"}