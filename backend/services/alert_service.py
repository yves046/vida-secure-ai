import os
import time

from database import SessionLocal
from models import Alert

from intrusion import record_video, frame_buffer

from incident_db import (
    find_open_incident,
    update_last_detection,
    save_incident,
)

from mailer import send_alert
from services.report_service import create_pdf_report


ALERT_EMAIL = "yvestoure717@gmail.com"

def create_alert(user_id, cap, detection):   

    incident = find_open_incident(
        user_id,
        "Zone 1"
    )

    if incident:

        print("Incident déjà ouvert")

        update_last_detection(
            incident[0]
        )

        return

    else:

        print("Nouvel incident")

        files = record_video(
            list(frame_buffer), 
            detection
        )

        if files is None:
            return

        video_filename = files["video"]
        image_filename = files["image"]

        db = SessionLocal()

        new_alert = Alert(
            user_id=user_id,
            message="Intrusion détectée",
            video_url=video_filename
        )

        db.add(new_alert)
        db.commit()
        db.close()

        print("CHEMIN VIDEO :", video_filename)

        incident_id = f"VIDA-{int(time.time())}"

        pdf_filename = create_pdf_report(image_filename)

        save_incident(
            user_id=user_id,
            camera_id=1,
            incident_id=incident_id,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            client_name="VIDA DEMO",
            site_name="Site Principal",
            zone_name="Zone 1",
            alert_level="INTRUSION",
            persons_count=1,
            intrusion_duration=0,
            pdf_path=pdf_filename,
            image_path=image_filename,
            video_path=video_filename
        )

        print("Nouvel incident créé")

        print("Incident enregistré dans VIDA DB")

        print("PDF :", pdf_filename)
        print("IMAGE :", image_filename)
        print("VIDEO :", video_filename)

        import os

        print("PDF EXISTE :", os.path.exists(pdf_filename))
        print("IMAGE EXISTE :", os.path.exists(image_filename))
        
        video_path = os.path.join("videos", video_filename)

        print("DOSSIER ACTUEL :", os.getcwd())
        print("CHEMIN VIDEO :", video_path)
        print("CHEMIN ABSOLU :", os.path.abspath(video_path))

        print("VIDEO EXISTE :", os.path.exists(video_path))

        if os.path.exists(video_path):
            print(
                "TAILLE VIDEO :",
                os.path.getsize(video_path),
                "octets"
            )

        print("VIDEO ENVOYÉE AU MAIL :", video_path)
        print("EXISTE :", os.path.exists(video_path))

        send_alert(
            to_email=ALERT_EMAIL,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            intrusion_duration=0,
            persons_count=1,
            pdf_path=pdf_filename,
            image_path=image_filename,
            video_path=video_path
        )

        print("EMAIL DEMANDE")   
