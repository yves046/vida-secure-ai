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
from zone_db import init_zone_db
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
init_zone_db()

# ==========================================
# File d'attente des incidents
# ==========================================


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
            .filter(models.Camera.status == "ACTIVE")
            .all()
        )
    finally:
        db.close()

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
                camera.rtsp_url,
                camera.user_id,
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
