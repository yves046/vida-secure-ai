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
from dotenv import load_dotenv

load_dotenv()

from routers.cameras import router as cameras_router
from routers.auth import router as auth_router
from routers.dashboard import router as dashboard_router
from routers.payments import router as payments_router
from services.report_service import create_pdf_report
from services.alert_service import create_alert


ALERT_EMAIL = "yvestoure717@gmail.com"

models.Base.metadata.create_all(bind=engine)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")

app = FastAPI()

app.include_router(cameras_router)
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(payments_router)

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
