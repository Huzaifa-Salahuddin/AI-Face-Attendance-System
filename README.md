# 🧑‍💼 AI Attendance Manager  

🚀 An AI-powered **face recognition attendance system** built with **FastAPI**, **DeepFace**, **MongoDB Atlas**, and fully containerized with **Docker**.  

This system eliminates **proxy attendance**, automates **check-ins/check-outs**, and sends **late check-in email alerts**. Perfect for modern organizations looking for **accuracy, automation, and scalability**.  

---

## ✨ Features  

- ✅ Face recognition-based **check-in/check-out**  
- ✅ Prevents **proxy attendance**  
- ✅ Real-time **late check-in alerts** via email  
- ✅ Admin dashboard for **managing users and attendance records**  
- ✅ **CSV export** for reports  
- ✅ **Dockerized** for easy deployment anywhere  

---

## 🛠️ Tech Stack  

- **FastAPI** – Backend framework  
- **DeepFace** – Face recognition library  
- **MongoDB Atlas** – Cloud database  
- **Docker** – Deployment  
- **aiosmtplib** – Async email service  
- **Jinja2** – HTML templates  

---

## 📂 Project Structure  

```bash
app/
 ├── routes/        # FastAPI routes (auth, admin, attendance)
 ├── services/      # Database, face recognition, email service
 ├── templates/     # HTML templates (login, dashboards)
 ├── static/        # CSS, JS, assets
 └── main.py        # Entry point
```
⚙️ Installation

Follow these steps to set up the project locally:

1. Clone the repository
```bash
git clone [https://github.com/your-username/ai-attendance-manager.git](https://github.com/Huzaifa-Salahuddin/Face_attendance)
cd ai-attendance-manager
```
3. Create a virtual environment  
```bash
python -m venv venv

```
3. Activate the environment  
Linux/Mac:
```bash
source venv/bin/activate
```
Windows:
```bash
venv\Scripts\activate
```
4. Install dependencies  
```bash
pip install -r requirements.txt
```
5. Run the application locally  
```bash
python -m uvicorn app.main:app --reload --port 8000
```
🐳 Docker Deployment  

Deploy easily using Docker:  

```bash
# Build the image
docker build -t face-app .
```
# Pull the prebuilt image from Docker Hub
```bash
docker pull huzaifa212/face-app
```
# Run the container (port 8000 → 8000)
```bash
docker run -p 8000:8000 huzaifa212/face-app:latest
```

# Check available images
```bash
docker images
```
# List running containers
```bash
docker ps
```

# Running containers and paste this url
```bash
http://127.0.0.1:8000
```
