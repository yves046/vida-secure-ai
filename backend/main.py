from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from models import Alert
from database import SessionLocal
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Form, HTTPException, Depends, Body, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from database import engine, SessionLocal
from fastapi.responses import FileResponse
from models import Base, User, Alert
from sqlalchemy.orm import Session
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import intrusion

from intrusion import (
    start_detection,
    record_video,
    frame_buffer
)
from incident_db import (
    init_incident_db,
    save_incident,
    find_open_incident,
    update_last_detection,
    close_old_incidents
)
from zone_db import init_zone_db
from camera_db import (
    add_camera,
    get_cameras,
    delete_camera,
    get_active_cameras
)
from mailer import send_alert
import time
import models
import threading
from queue import Queue
import os
import requests
import hmac
import hashlib
import sqlite3
from zones import load_camera_zones


from database import engine
from security import hash_password, verify_password, create_access_token
from deps import get_db, get_current_user
from datetime import timedelta
from routers.cameras import router as cameras_router
from services.report_service import create_pdf_report
from services.alert_service import create_alert
from dotenv import load_dotenv


ALERT_EMAIL = "yvestoure717@gmail.com"

models.Base.metadata.create_all(bind=engine)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv()

PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")

app = FastAPI()

app.include_router(cameras_router)

init_incident_db()
init_zone_db()

# ==========================================
# File d'attente des incidents
# ==========================================

incident_queue = Queue()

import os
import cv2

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

def generate_frames():

    zones = load_camera_zones(1)

    while True:

        if intrusion.latest_frame is None:
            time.sleep(0.01)
            continue

        with intrusion.frame_lock:
            frame = intrusion.latest_frame.copy()

        for zone in zones:

            pts = np.array(zone["points"], np.int32)
            pts = pts.reshape((-1, 1, 2))

            cv2.polylines(
                frame,
                [pts],
                True,
                (0, 0, 255),
                2
            )

            cv2.putText(
                frame,
                zone["name"],
                tuple(pts[0][0]),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 255),
                2
            )

        ok, buffer = cv2.imencode(".jpg", frame)

        if not ok:
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + buffer.tobytes()
            + b"\r\n"
        )

@app.get("/video_feed")
def video_feed():
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/")
def home():
    return {"message": "VIDA Secure AI Backend Online"}

os.makedirs(os.path.join(BASE_DIR, "videos"), exist_ok=True)

app.mount(
    "/videos",
    StaticFiles(directory=os.path.join(BASE_DIR, "videos")),
    name="videos"
)

app.mount(
    "/images",
    StaticFiles(directory=BASE_DIR),
    name="images"
)

app.mount(
    "/pdfs",
    StaticFiles(directory=BASE_DIR),
    name="pdfs"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================== ROUTES AUTH =====================
@app.post("/register")
def register(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()

    if user is not None:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")

    new_user = models.User(
        email=email,
        password_hash=hash_password(password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "Utilisateur créé"}


@app.post("/login")
def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    email = username

    user = (
        db.query(models.User)
        .filter(models.User.email == email)
        .first()
    )

    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Identifiants invalides"
        )

    token = create_access_token(
        {"sub": str(user.id)}
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }

@app.post("/test-alert")
def test_alert(
    data: dict,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    alert = models.Alert(
        user_id=user.id,
        message=data.get("message"),
        video_url=data.get("video_url"),
        timestamp=datetime.utcnow()
    )

    db.add(alert)
    db.commit()

    return {"status": "saved"}

@app.get("/dashboard")
def dashboard(user: models.User = Depends(get_current_user)):

    print("========== USER CONNECTÉ ==========")
    print("ID :", user.id)
    print("EMAIL :", user.email)
    print("PAID :", user.paid)
    print("===================================")

    return {
        "message": "Bienvenue !",
        "email": user.email
    }


@app.get("/stats")
def get_stats(
    user: models.User = Depends(get_current_user)
):

    conn = sqlite3.connect("vida_incidents.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM incidents"
    )

    total_alerts = cursor.fetchone()[0]

    conn.close()

    return {
        "cameras": 1,
        "alerts": total_alerts,
        "status": "ACTIVE",
        "paid": user.paid
    }

@app.get("/alerts")
def get_alerts(
    current_user: models.User = Depends(get_current_user)
):

    # 🔒 Vérification abonnement
    if not current_user.paid:
        raise HTTPException(
            status_code=403,
            detail="Abonnement requis"
        )

    conn = sqlite3.connect("vida_incidents.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    print(
        "ALERTS POUR USER =",
        current_user.id
    )

    cursor.execute("""
        SELECT *
        FROM incidents
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 20
    """, (current_user.id,)) 

    incidents = cursor.fetchall()

    conn.close()

    return [
        {
            "id": row["incident_id"],
            "type": row["alert_level"],
            "zone": row["zone_name"],
            "persons": row["persons_count"],
            "timestamp": row["timestamp"],

            "image":row["image_path"],
            "video": row["video_path"],
            "pdf": row["pdf_path"]
        }
        for row in incidents
    ]

@app.get("/payment-success")
def payment_success(reference: str, db: Session = Depends(get_db)):
    url = f"https://api.paystack.co/transaction/verify/{reference}"

    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"
    }

    response = requests.get(url, headers=headers)
    data = response.json()

    if data["data"]["status"] == "success":
        email = data["data"]["customer"]["email"]

        user = db.query(models.User).filter(models.User.email == email).first()

        if user:
            user.paid = True
            user.paid_until = datetime.utcnow() + timedelta(days=30)
            db.commit()

        return {"message": "Paiement validé"}

    return {"message": "Paiement échoué"}

@app.get("/activate-payment")
def activate_payment(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    user.paid = True
    db.commit()
    return {"message": "Paiement activé"}

@app.get("/payment-success")
def payment_success():
    return {"message": "Paiement reçu avec succès"}

@app.get("/secure-video/{filename}")
def get_video(
    filename: str,
    current_user: models.User = Depends(get_current_user)
):
    
    if not current_user.paid:
        raise HTTPException(status_code=403, detail="Abonnement requis")

    filepath = f"videos/{filename}"

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Vidéo introuvable")

    return FileResponse(filepath, media_type="video/mp4")

# ===================== TEST ALERT (photo + vidéo + PDF) =====================
@app.post("/test-alert")
def test_alert():
    user = db.query(User).first()  # ou ton vrai filtre

    if not user:
        return {"error": "User non trouvé"}

    if not user.paid:
        return {"error": "Utilisateur non abonné"}

    return {"message": "Alerte envoyée"}

def send_alert_email(to_email: str, photo_path: str, clip_path: str, pdf_path: str, timestamp: str):
    msg = MIMEMultipart()
    msg["From"] = os.getenv("EMAIL_USER")
    msg["To"] = to_email
    msg["Subject"] = f"Alerte Intrusion - {timestamp}"

    body = f"Alerte intrusion détectée à {timestamp}\n\nFichiers joints :"
    msg.attach(MIMEText(body, "plain"))

    # Photo
    if os.path.exists(photo_path):
        with open(photo_path, "rb") as f:
            msg.attach(MIMEImage(f.read(), name=f"photo_{timestamp}.jpg"))

    # Clip
    if os.path.exists(clip_path):
        with open(clip_path, "rb") as f:
            part = MIMEApplication(f.read(), _subtype="mp4")
            part.add_header("Content-Disposition", "attachment", filename=f"clip_{timestamp}.mp4")
            msg.attach(part)

    # PDF
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            part = MIMEApplication(f.read(), _subtype="pdf")
            part.add_header("Content-Disposition", "attachment", filename=f"report_{timestamp}.pdf")
            msg.attach(part)

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASSWORD"))
        server.send_message(msg)
        server.quit()
        print(f"Email envoyé à {to_email}")
    except Exception as e:
        print(f"Erreur email: {e}")

@app.post("/init-payment")
def init_payment(user: models.User = Depends(get_current_user)):
    url = "https://api.paystack.co/transaction/initialize"
    
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
            
    data = {
        "email": user.email,
        "amount": 5000 * 100,
        "callback_url": "http://localhost:8501/?payment=success"
    }
            
    response = requests.post(url, json=data, headers=headers)

    print("PAYSTACK RESPONSE:", response.text)  # 🔴 debug

    return response.json()

@app.post("/paystack/webhook")
async def paystack_webhook(
    request: Request,
    db: Session = Depends(get_db)
):

    payload = await request.body()

    signature = request.headers.get("x-paystack-signature")

    computed_signature = hmac.new(
        PAYSTACK_SECRET_KEY.encode(),
        payload,
        hashlib.sha512
    ).hexdigest()

    if signature != computed_signature:
        raise HTTPException(
            status_code=400,
            detail="Signature invalide"
        )

    event = await request.json()

    if event["event"] == "charge.success":

        email = event["data"]["customer"]["email"]

        user = db.query(models.User).filter(
            models.User.email == email
        ).first()

        if user:

            user.paid = True

            db.commit()

            print(f"PAIEMENT ACTIVE POUR : {email}")

    return {"status": "success"}

def incident_maintenance():
     
     while True:
         
         print("Vérification des incidents...")

         close_old_incidents()

         time.sleep(30)


@app.on_event("startup")
def start_camera():

    conn = sqlite3.connect("vida_incidents.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM cameras
        WHERE status = 'ACTIVE'
    """)

    cameras = cursor.fetchall()

    conn.close()

    print("=" * 50)
    print(f"CAMÉRAS TROUVÉES : {len(cameras)}")
    print("=" * 50)

    for camera in cameras:

        print(
            f"Lancement : {camera['name']}"
        )

        thread = threading.Thread(
            target=start_detection,
            args=(
                camera["rtsp_url"],
                camera["user_id"],
                create_alert
            )
        )

        thread.daemon = True
        thread.start()

    print("=" * 50)
    print("SURVEILLANCE DÉMARRÉE")
    print("=" * 50)

    maintenance_thread = threading.Thread(
        target=incident_maintenance
    )

    maintenance_thread.daemon = True
    maintenance_thread.start()

    print("Maintenance des incidents démarrée")
