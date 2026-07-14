import sqlite3
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import StreamingResponse
from database import engine, SessionLocal
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import intrusion

from intrusion import start_detection
from incident_db import init_incident_db, close_old_incidents
import time
import models
import threading
import os
from zones import load_camera_zones


from database import engine
from deps import get_current_user
from dotenv import load_dotenv

load_dotenv()

from routers.cameras import router as cameras_router
from routers.auth import router as auth_router
from routers.dashboard import router as dashboard_router
from routers.payments import router as payments_router
from services.alert_service import create_alert



models.Base.metadata.create_all(bind=engine)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


app = FastAPI()

app.include_router(cameras_router)
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(payments_router)

init_incident_db()

# ==========================================
# File d'attente des incidents
# ==========================================


import os
import cv2

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

def generate_frames(camera_id):

    state = intrusion.get_camera_state(camera_id)
    frame_lock = state["frame_lock"]

    zones = []
    last_zones_reload = 0
    ZONES_RELOAD_INTERVAL = 2

    while True:

        now = time.time()

        if now - last_zones_reload >= ZONES_RELOAD_INTERVAL:
            zones = load_camera_zones(camera_id)
            last_zones_reload = now

        with frame_lock:
            if state["latest_frame"] is None:
                frame = None
            else:
                frame = state["latest_frame"].copy()

        if frame is None:
            time.sleep(0.01)
            continue

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


@app.get("/video_feed/{camera_id}")
def video_feed(camera_id: int):
    return StreamingResponse(
        generate_frames(camera_id),
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

@app.get("/secure-video/{filename}")
def get_video(
    filename: str,
    current_user: models.User = Depends(get_current_user)
):

    if not current_user.paid:
        raise HTTPException(
            status_code=403,
            detail="Abonnement requis"
        )

    safe_filename = os.path.basename(filename)
    filepath = os.path.join("videos", safe_filename)

    conn = sqlite3.connect("vida_incidents.db")
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id
            FROM incidents
            WHERE user_id = ?
            AND (
                video_path = ?
                OR video_path = ?
            )
            LIMIT 1
            """,
            (
                current_user.id,
                safe_filename,
                filepath
            )
        )

        incident = cursor.fetchone()

    finally:
        conn.close()

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Vidéo introuvable"
        )

    if not os.path.isfile(filepath):
        raise HTTPException(
            status_code=404,
            detail="Fichier vidéo introuvable"
        )

    return FileResponse(
        filepath,
        media_type="video/mp4",
        filename=safe_filename
    )

@app.get("/secure-image/{filename}")
def get_image(
    filename: str,
    current_user: models.User = Depends(get_current_user)
):
    if not current_user.paid:
        raise HTTPException(
            status_code=403,
            detail="Abonnement requis"
        )

    safe_filename = os.path.basename(filename)

    conn = sqlite3.connect("vida_incidents.db")
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT image_path
            FROM incidents
            WHERE user_id = ?
            AND image_path = ?
            LIMIT 1
            """,
            (current_user.id, safe_filename)
        )

        incident = cursor.fetchone()

    finally:
        conn.close()

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Image introuvable"
        )

    filepath = incident[0]

    if not os.path.isfile(filepath):
        raise HTTPException(
            status_code=404,
            detail="Fichier image introuvable"
        )

    return FileResponse(
        filepath,
        media_type="image/jpeg",
        filename=safe_filename
    )


@app.get("/secure-pdf/{filename}")
def get_pdf(
    filename: str,
    current_user: models.User = Depends(get_current_user)
):
    if not current_user.paid:
        raise HTTPException(
            status_code=403,
            detail="Abonnement requis"
        )

    safe_filename = os.path.basename(filename)

    conn = sqlite3.connect("vida_incidents.db")
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT pdf_path
            FROM incidents
            WHERE user_id = ?
            AND pdf_path = ?
            LIMIT 1
            """,
            (current_user.id, safe_filename)
        )

        incident = cursor.fetchone()

    finally:
        conn.close()

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="PDF introuvable"
        )

    filepath = incident[0]

    if not os.path.isfile(filepath):
        raise HTTPException(
            status_code=404,
            detail="Fichier PDF introuvable"
        )

    return FileResponse(
        filepath,
        media_type="application/pdf",
        filename=safe_filename
    )


def incident_maintenance():
     
     while True:
         
         print("Vérification des incidents...")

         close_old_incidents()

         time.sleep(30)


@app.on_event("startup")
def start_camera():

    db = SessionLocal()

    try:
        cameras = (
            db.query(models.Camera)
            .filter(models.Camera.status != "INACTIVE")
            .all()
        )
    finally:
        db.close()

    print("=" * 50)
    print(f"CAMÉRAS TROUVÉES : {len(cameras)}")
    print("=" * 50)

    for camera in cameras:

        print(
            f"Lancement : {camera.name}"
        )

        thread = threading.Thread(
            target=start_detection,
            args=(
                camera.rtsp_url,
                camera.user_id,
                camera.id,
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
