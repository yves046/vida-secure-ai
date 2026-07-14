import os
import time

from intrusion import record_video, get_camera_state

from incident_db import (
    find_open_incident,
    update_last_detection,
    save_incident,
)

from mailer import send_alert
from services.report_service import create_pdf_report
from database import SessionLocal
from models import Camera, User


ALERT_EMAIL = "yvestoure717@gmail.com"

def create_alert(
    user_id,
    camera_id,
    zone_name,
    persons_count,
    intrusion_duration,
    detection
):   

    db = SessionLocal()

    try:
        camera = (
            db.query(Camera)
            .filter(
                Camera.id == camera_id,
                Camera.user_id == user_id
            )
            .first()
        )

        user = (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )

        if camera is None:
            print(
                f"ERREUR : caméra {camera_id} introuvable "
                f"pour l'utilisateur {user_id}."
            )
            return

        client_name = (
            user.email
            if user is not None
            else f"Client VIDA #{user_id}"
        )

        site_name = (
            camera.site_name
            or camera.location
            or camera.name
            or f"Caméra #{camera_id}"
        )

    finally:
        db.close()

    incident = find_open_incident(
        user_id,
        camera_id,
        zone_name
    )

    if incident:

        print("Incident déjà ouvert")

        update_last_detection(
            incident[0]
        )

        return

    else:

        print("Nouvel incident")

        state = get_camera_state(camera_id)

        files = record_video(
            list(state["frame_buffer"]),
            detection
        )

        if files is None:
            return

        video_path = files["video"]
        image_filename = files["image"]

        print("CHEMIN VIDEO :", video_path)

        incident_id = f"VIDA-{int(time.time())}"

        if persons_count >= 3:
            alert_level = "CRITIQUE"
        elif persons_count == 2:
            alert_level = "ÉLEVÉ"
        else:
            alert_level = "MODÉRÉ"

        pdf_filename = create_pdf_report(
            image_path=image_filename,
            incident_id=incident_id,
            client_name=client_name,
            site_name=site_name,
            zone_name=zone_name,
            persons_count=persons_count,
            intrusion_duration=intrusion_duration,
            alert_level=alert_level
        )

        save_incident(
            user_id=user_id,
            camera_id=camera_id,
            incident_id=incident_id,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            client_name=client_name,
            site_name=site_name,
            zone_name=zone_name,
            alert_level=alert_level,
            persons_count=persons_count,
            intrusion_duration=intrusion_duration,
            pdf_path=pdf_filename,
            image_path=image_filename,
            video_path=video_path
        )

        print("Nouvel incident créé")

        print("Incident enregistré dans VIDA DB")

        print("PDF :", pdf_filename)
        print("IMAGE :", image_filename)
        print("VIDEO :", video_path)

        import os

        print("PDF EXISTE :", os.path.exists(pdf_filename))
        print("IMAGE EXISTE :", os.path.exists(image_filename))
        

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
            intrusion_duration=intrusion_duration,
            persons_count=persons_count,
            pdf_path=pdf_filename,
            image_path=image_filename,
            video_path=video_path
        )

        print("EMAIL DEMANDE")   
