# from motor.motor_asyncio import AsyncIOMotorClient

# # Corrected MONGO_URI without angle brackets
# MONGO_URI = "mongodb+srv://arcanainfo:arcanainfo123@attendance.ttgqsop.mongodb.net/?retryWrites=true&w=majority&appName=attendance"

# client = AsyncIOMotorClient(MONGO_URI)
# db = client["attendance_db"]


import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
MONGO_URI = "mongodb+srv://huzaifa:huzaifa2001@ats.vz3ywzy.mongodb.net/?retryWrites=true&w=majority&appName=ats"
client = AsyncIOMotorClient(MONGO_URI)
db = client["attendance_db"]

# import os
# from motor.motor_asyncio import AsyncIOMotorClient
# from dotenv import load_dotenv
# import atexit

# load_dotenv()

# # Use your MongoDB Atlas connection string
# # Replace <db_password> with your actual password
# MONGODB_URL = os.getenv("mongodb+srv://huzaifaarain424_db_user:<db_password>@ats.vz3ywzy.mongodb.net/?retryWrites=true&w=majority&appName=ats")
# DATABASE_NAME = os.getenv("DATABASE_NAME", "attendance_system")

# # Global variables
# client = None
# db = None

# def get_database():
#     global client, db
    
#     if db is not None:
#         return db
    
#     try:
#         print(f"🔗 Connecting to MongoDB Atlas...")
#         client = AsyncIOMotorClient(
#             MONGODB_URL,
#             serverSelectionTimeoutMS=10000,  # 10 second timeout
#             connectTimeoutMS=10000
#         )
#         db = client[DATABASE_NAME]
        
#         # Test connection synchronously for simplicity
#         import asyncio
#         async def test_connection():
#             try:
#                 await client.admin.command('ping')
#                 print("✅ Successfully connected to MongoDB Atlas!")
#                 print("📍 Connected to cluster: ats.vz3ywzy.mongodb.net")
#                 return True
#             except Exception as e:
#                 print(f"❌ Connection test failed: {e}")
#                 return False
        
#         # Run the connection test
#         success = asyncio.run(test_connection())
        
#         if not success:
#             raise Exception("Connection test failed")
        
#         return db
        
#     except Exception as e:
#         print(f"❌ MongoDB Atlas connection failed: {e}")
#         print("⚠️ Please check your .env file and MongoDB Atlas settings")
#         print("💡 Make sure to:")
#         print("   1. Replace 'your_password_here' with your actual password")
#         print("   2. Check your Atlas cluster IP whitelist")
#         print("   3. Verify your database user credentials")
        
#         # Exit or use fallback - you choose
#         # For development, you might want to exit
#         exit(1)

# # Initialize database connection
# db = get_database()

# # Cleanup function
# def close_connection():
#     if client:
#         client.close()
#         print("Database connection closed")

# atexit.register(close_connection)


