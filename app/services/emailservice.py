# import os
# import smtplib
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
# from dotenv import load_dotenv

# # Load environment variables
# load_dotenv()

# class EmailService:
#     def __init__(self):
#         self.email_address = os.getenv("EMAIL_ADDRESS")
#         self.email_password = os.getenv("EMAIL_PASSWORD")
#         self.email_host = os.getenv("EMAIL_HOST", "smtp.gmail.com")
#         self.email_port = int(os.getenv("EMAIL_PORT", 587))
        
#         if not self.email_address or not self.email_password:
#             raise ValueError("EMAIL_ADDRESS and EMAIL_PASSWORD must be set in environment variables")
    
#     async def send_late_checkin_email(self, to_email, name, checkin_time):
#         try:
#             # Email content
#             subject = "Late Check-In Notification"
#             body = f"""
#             Dear {name},
            
#             You have checked in late at {checkin_time}. 
#             Please ensure you maintain punctuality.
            
#             Best regards,
#             Attendance System
#             """
            
#             # Create message
#             msg = MIMEMultipart()
#             msg['From'] = self.email_address
#             msg['To'] = to_email
#             msg['Subject'] = subject
#             msg.attach(MIMEText(body, 'plain'))
            
#             # Send email
#             with smtplib.SMTP(self.email_host, self.email_port) as server:
#                 server.starttls()
#                 server.login(self.email_address, self.email_password)
#                 server.send_message(msg)
            
#             return True
            
#         except Exception as e:
#             print(f"Email sending failed: {e}")
#             return False

# # Create a global instance but don't initialize it yet
# _email_service = None

# def get_email_service():
#     global _email_service
#     if _email_service is None:
#         try:
#             _email_service = EmailService()
#             print("✅ Email service initialized successfully")
#         except ValueError as e:
#             print(f"❌ Email service not available: {e}")
#             _email_service = None
#     return _email_service

# # Function to send late check-in email
# async def send_late_checkin_email(to_email, name, checkin_time):
#     email_service = get_email_service()
#     if email_service is None:
#         print("⚠️ Email service not configured - skipping email notification")
#         return False
    
#     return await email_service.send_late_checkin_email(to_email, name, checkin_time)
import os
import aiosmtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class EmailService:
    def __init__(self):
        self.email_address = os.getenv("EMAIL_ADDRESS")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        self.email_host = os.getenv("EMAIL_HOST", "smtp.gmail.com")
        self.email_port = int(os.getenv("EMAIL_PORT", 465))  # Default to SSL port
        
        if not self.email_address or not self.email_password:
            raise ValueError("EMAIL_ADDRESS and EMAIL_PASSWORD must be set in environment variables")
    
    async def send_late_checkin_email(self, to_email, name, checkin_time):
        try:
            # Email content
            subject = "Late Check-In Notification"
            body = f"""Dear  {name},

Our records show that you checked in late at {checkin_time} today.

We kindly remind you to adhere to your scheduled start time and maintain punctuality moving forward. Consistent timeliness helps ensure smooth operations and reflects positively on your professional commitment.

If there are any concerns or unavoidable circumstances affecting your arrival time, please feel free to inform your supervisor or HR.

Thank you for your attention to this matter.

Best regards,
Attendance System
            """
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            # Create SSL context
            ssl_context = ssl.create_default_context()
            
            # Try different connection methods
            try:
                # Method 1: Try SSL connection (port 465)
                print(f"🔗 Attempting SSL connection to {self.email_host}:465...")
                await aiosmtplib.send(
                    msg,
                    hostname=self.email_host,
                    port=465,
                    use_tls=True,
                    tls_context=ssl_context,
                    username=self.email_address,
                    password=self.email_password,
                    timeout=30
                )
                print("✅ Email sent via SSL (port 465)")
                
            except Exception as ssl_error:
                print(f"⚠️ SSL connection failed: {ssl_error}. Trying STARTTLS...")
                
                # Method 2: Try STARTTLS (port 587)
                try:
                    print(f"🔗 Attempting STARTTLS connection to {self.email_host}:587...")
                    await aiosmtplib.send(
                        msg,
                        hostname=self.email_host,
                        port=587,
                        start_tls=True,
                        username=self.email_address,
                        password=self.email_password,
                        timeout=30
                    )
                    print("✅ Email sent via STARTTLS (port 587)")
                    
                except Exception as tls_error:
                    print(f"⚠️ STARTTLS connection failed: {tls_error}. Trying direct connection...")
                    
                    # Method 3: Try without SSL (for testing only - not recommended)
                    try:
                        print(f"🔗 Attempting plain connection to {self.email_host}:587...")
                        await aiosmtplib.send(
                            msg,
                            hostname=self.email_host,
                            port=587,
                            start_tls=False,
                            username=self.email_address,
                            password=self.email_password,
                            timeout=30
                        )
                        print("✅ Email sent via plain connection")
                        
                    except Exception as plain_error:
                        print(f"❌ All connection methods failed: {plain_error}")
                        raise plain_error
            
            print(f"✅ Late check-in email sent to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Email sending failed to {to_email}: {e}")
            
            # Provide helpful debugging information
            if "authentication" in str(e).lower():
                print("💡 Authentication failed. Please check:")
                print("   - Are you using an App Password (not your regular password)?")
                print("   - Is 2-factor authentication enabled?")
                print("   - Are your credentials correct?")
            elif "connection" in str(e).lower() or "ssl" in str(e).lower():
                print("💡 Connection failed. Please check:")
                print("   - Is your internet connection working?")
                print("   - Are you using the correct port (465 for SSL, 587 for TLS)?")
                print("   - Does your firewall allow SMTP connections?")
            
            return False

# Create a global instance but don't initialize it yet
_email_service = None

def get_email_service():
    global _email_service
    if _email_service is None:
        try:
            _email_service = EmailService()
            print("✅ Email service initialized successfully")
            print(f"   Using: {_email_service.email_address}")
            print(f"   Host: {_email_service.email_host}")
            print(f"   Port: {_email_service.email_port}")
        except ValueError as e:
            print(f"❌ Email service not available: {e}")
            print("💡 Please set EMAIL_ADDRESS and EMAIL_PASSWORD in your .env file")
            _email_service = None
    return _email_service

# Function to send late check-in email
async def send_late_checkin_email(to_email, name, checkin_time):
    email_service = get_email_service()
    if email_service is None:
        print("⚠️ Email service not configured - skipping email notification")
        return False
    
    print(f"📧 Attempting to send late check-in email to {to_email}...")
    return await email_service.send_late_checkin_email(to_email, name, checkin_time)