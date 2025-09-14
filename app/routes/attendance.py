# from fastapi import APIRouter, UploadFile, File, Request, Form
# from fastapi.templating import Jinja2Templates
# from fastapi.responses import HTMLResponse
# from app.services.db import db
# from app.services.face_service import quick_face_verify as verify_faces
# try:
#     from app.services.emailservice import send_late_checkin_email
# except Exception as e:
#     print(f"Email service not available: {e}")
#     # Create a dummy function
#     async def send_late_checkin_email(*args, **kwargs):
#         print("⚠️ Email service not configured - skipping email")
#         return False # Import email service
# from datetime import datetime
# import pytz
# from app.routes.auth import active_sessions
# from fastapi.responses import RedirectResponse


# router = APIRouter()
# templates = Jinja2Templates(directory="app/templates")

# @router.get("/attendance", response_class=HTMLResponse)
# async def attendance_form(request: Request, msg: str = ""):
#     session_id = request.cookies.get("session_id")
#     if not session_id or session_id not in active_sessions:
#         return RedirectResponse(url="/login", status_code=302)

#     user_session = active_sessions[session_id]
#     return templates.TemplateResponse("user_attendance.html", {"request": request, "msg": msg})


# @router.post("/attendance")
# async def mark_attendance(
#     request: Request,
#     image: UploadFile = File(...),
#     action: str = Form(...)
# ):
#     # Session validation
#     session_id = request.cookies.get("session_id")
#     if not session_id or session_id not in active_sessions:
#         return RedirectResponse(url="/login", status_code=302)

#     user_session = active_sessions[session_id]
    
#     # Read and validate image
#     image_data = await image.read()
#     if not image_data or len(image_data) < 1000:
#         return {
#             "status": "error",
#             "message": "❌ Invalid or empty image uploaded."
#         }

#     # Face recognition process
#     users = await db.users.find().to_list(100)
#     for user in users:
#         if "face_image" not in user:
#             continue

#         is_verified, distance = verify_faces(user["face_image"], image_data)

#         if is_verified:
#             # Get Pakistan timezone
#             pakistan_time = datetime.now(pytz.timezone("Asia/Karachi"))
#             date_str = pakistan_time.strftime("%Y-%m-%d")
#             time_str = pakistan_time.strftime("%H:%M:%S")

#             # Check for existing attendance record
#             existing_record = await db.attendance.find_one({
#                 "user_id": str(user["_id"]),
#                 "date": date_str
#             })

#             # ✅ CHECK-IN LOGIC WITH EMAIL
#             if action == "checkin":
#                 # Check if user is late (after 9:30 AM)
#                 is_late = pakistan_time.time() > datetime.strptime("09:00:00", "%H:%M:%S").time()

#                 if existing_record:
#                     if existing_record.get("checkin"):
#                         # Already checked in - don't overwrite
#                         return {
#                             "status": "info",
#                             "message": f"✅ Already checked in at {existing_record['checkin']}."
#                         }
#                     else:
#                         # Update existing record with check-in
#                         await db.attendance.update_one(
#                             {"_id": existing_record["_id"]},
#                             {"$set": {
#                                 "checkin": time_str,
#                                 "late": is_late,
#                                 "status": "Present" + (" (Late)" if is_late else "")
#                             }}
#                         )
                        
#                         # 📧 SEND LATE CHECK-IN EMAIL
#                         if is_late:
#                             try:
#                                 email_sent = await send_late_checkin_email(
#                                     user["email"], 
#                                     user["name"], 
#                                     time_str
#                                 )
#                                 if email_sent:
#                                     print(f"✅ Late check-in email sent to {user['email']}")
#                                 else:
#                                     print(f"⚠️ Failed to send late check-in email to {user['email']}")
#                             except Exception as e:
#                                 print(f"❌ Email service error: {e}")
#                                 # Don't let email failure affect attendance recording
#                 else:
#                     # Create new attendance record
#                     await db.attendance.insert_one({
#                         "user_id": str(user["_id"]),
#                         "name": user["name"],
#                         "email": user["email"],
#                         "date": date_str,
#                         "checkin": time_str,
#                         "checkout": None,
#                         "late": is_late,
#                         "status": "Present" + (" (Late)" if is_late else "")
#                     })
                    
#                     # 📧 SEND LATE CHECK-IN EMAIL
#                     if is_late:
#                         try:
#                             email_sent = await send_late_checkin_email(
#                                 user["email"], 
#                                 user["name"], 
#                                 time_str
#                             )
#                             if email_sent:
#                                 print(f"✅ Late check-in email sent to {user['email']}")
#                             else:
#                                 print(f"⚠️ Failed to send late check-in email to {user['email']}")
#                         except Exception as e:
#                             print(f"❌ Email service error: {e}")
#                             # Don't let email failure affect attendance recording

#                 return {
#                     "status": "success",
#                     "message": f"✅ Check-In marked for {user['name']}{' (Late)' if is_late else ''}"
#                     + (" - Email notification sent!" if is_late else "")
#                 }

#             # ✅ CHECK-OUT LOGIC (unchanged)
#             elif action == "checkout":
#                 if existing_record:
#                     await db.attendance.update_one(
#                         {"_id": existing_record["_id"]},
#                         {"$set": {
#                             "checkout": time_str
#                         }}
#                     )
#                     return {
#                         "status": "success",
#                         "message": f"✅ Check-Out updated for {user['name']} at {time_str}"
#                     }
#                 else:
#                     # Insert checkout-only entry
#                     await db.attendance.insert_one({
#                         "user_id": str(user["_id"]),
#                         "name": user["name"],
#                         "email": user["email"],
#                         "date": date_str,
#                         "checkin": None,
#                         "checkout": time_str,
#                         "late": False,
#                         "status": "-"
#                     })
#                     return {
#                         "status": "success",
#                         "message": f"⚠️ No Check-In found. Check-Out recorded for {user['name']}."
#                     }

#     # Face not recognized
#     return {
#         "status": "error",
#         "message": "❌ Face not recognized in the system."
#     }
from fastapi import APIRouter, UploadFile, File, Request, Form, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from app.services.db import db
from app.services.face_service import quick_face_verify as verify_faces
try:
    from app.services.emailservice import send_late_checkin_email
except Exception as e:
    print(f"Email service not available: {e}")
    # Create a dummy function
    async def send_late_checkin_email(*args, **kwargs):
        print("⚠️ Email service not configured - skipping email")
        return False
from datetime import datetime
import pytz
from app.routes.auth import active_sessions
from fastapi.responses import RedirectResponse

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/attendance", response_class=HTMLResponse)
async def attendance_form(request: Request, msg: str = ""):
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in active_sessions:
        return RedirectResponse(url="/login", status_code=302)

    user_session = active_sessions[session_id]
    return templates.TemplateResponse("user_attendance.html", {"request": request, "msg": msg})

@router.post("/attendance")
async def mark_attendance(
    request: Request,
    background_tasks: BackgroundTasks,  # Add this parameter
    image: UploadFile = File(...),
    action: str = Form(...)
):
    # Session validation
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in active_sessions:
        return RedirectResponse(url="/login", status_code=302)

    user_session = active_sessions[session_id]
    
    # Read and validate image
    image_data = await image.read()
    if not image_data or len(image_data) < 1000:
        return {
            "status": "error",
            "message": "❌ Invalid or empty image uploaded."
        }

    # Face recognition process
    users = await db.users.find().to_list(100)
    for user in users:
        if "face_image" not in user:
            continue

        is_verified, distance = verify_faces(user["face_image"], image_data)

        if is_verified:
            # Get Pakistan timezone
            pakistan_time = datetime.now(pytz.timezone("Asia/Karachi"))
            date_str = pakistan_time.strftime("%Y-%m-%d")
            time_str = pakistan_time.strftime("%H:%M:%S")

            # Check for existing attendance record
            existing_record = await db.attendance.find_one({
                "user_id": str(user["_id"]),
                "date": date_str
            })

            # ✅ CHECK-IN LOGIC WITH EMAIL
            if action == "checkin":
                # Check if user is late (after 9:00 AM)
                is_late = pakistan_time.time() > datetime.strptime("09:00:00", "%H:%M:%S").time()

                if existing_record:
                    if existing_record.get("checkin"):
                        # Already checked in - don't overwrite
                        return {
                            "status": "info",
                            "message": f"✅ Already checked in at {existing_record['checkin']}."
                        }
                    else:
                        # Update existing record with check-in
                        await db.attendance.update_one(
                            {"_id": existing_record["_id"]},
                            {"$set": {
                                "checkin": time_str,
                                "late": is_late,
                                "status": "Present" + (" (Late)" if is_late else "")
                            }}
                        )
                else:
                    # Create new attendance record
                    await db.attendance.insert_one({
                        "user_id": str(user["_id"]),
                        "name": user["name"],
                        "email": user["email"],
                        "date": date_str,
                        "checkin": time_str,
                        "checkout": None,
                        "late": is_late,
                        "status": "Present" + (" (Late)" if is_late else "")
                    })

                # 📧 SEND LATE CHECK-IN EMAIL IN BACKGROUND (USER WON'T SEE STATUS)
                if is_late:
                    background_tasks.add_task(
                        send_late_checkin_email,
                        user["email"], 
                        user["name"], 
                        time_str
                    )
                    # Email is sent in background, no status shown to user

                return {
                    "status": "success",
                    "message": f"✅ Check-In marked for {user['name']}{' (Late)' if is_late else ''}"
                }

            # ✅ CHECK-OUT LOGIC
            elif action == "checkout":
                if existing_record:
                    await db.attendance.update_one(
                        {"_id": existing_record["_id"]},
                        {"$set": {
                            "checkout": time_str
                        }}
                    )
                    return {
                        "status": "success",
                        "message": f"✅ Check-Out updated for {user['name']} at {time_str}"
                    }
                else:
                    # Insert checkout-only entry
                    await db.attendance.insert_one({
                        "user_id": str(user["_id"]),
                        "name": user["name"],
                        "email": user["email"],
                        "date": date_str,
                        "checkin": None,
                        "checkout": time_str,
                        "late": False,
                        "status": "-"
                    })
                    return {
                        "status": "success",
                        "message": f"⚠️ No Check-In found. Check-Out recorded for {user['name']}."
                    }

    # Face not recognized
    return {
        "status": "error",
        "message": "❌ Face not recognized in the system."
    }