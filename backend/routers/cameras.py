import threading

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

import models

from deps import get_db, get_current_user
from intrusion import (
    start_detection,
    stop_camera_detection,
    wait_for_camera_detection_stop,
)
from services.alert_service import create_alert


router = APIRouter(
    prefix="/cameras",
    tags=["Cameras"]
)

@router.get("")
def list_cameras(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    cameras = (
        db.query(models.Camera)
        .filter(models.Camera.user_id == current_user.id)
        .all()
    )

    return [
        {
            "id": camera.id,
            "camera_name": camera.name,
            "rtsp_url": camera.rtsp_url,
            "is_enabled": camera.is_enabled,
            "status": camera.status,
            "site_name": camera.site_name,
            "location": camera.location
        }
        for camera in cameras
    ]

@router.post("")
def add_camera(
    data: dict = Body(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # Vérifie si la caméra existe déjà
    existing = (
        db.query(models.Camera)
        .filter(
            models.Camera.user_id == current_user.id,
            models.Camera.rtsp_url == data["rtsp_url"]
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Cette caméra est déjà enregistrée."
        )

    # Création de la caméra
    camera = models.Camera(
        user_id=current_user.id,
        name=data["camera_name"],
        rtsp_url=data["rtsp_url"],
        is_enabled=True,
        status="OFFLINE",
        site_name=data.get("site_name"),
        location=data.get("location"),
        description=data.get("description"),
        zones_json="[]"
    )

    db.add(camera)
    db.commit()
    db.refresh(camera)

    print("=" * 40)
    print("NOUVELLE CAMÉRA")
    print("Nom :", camera.name)
    print("RTSP :", camera.rtsp_url)
    print("=" * 40)

    thread = threading.Thread(
        target=start_detection,
        args=(
            camera.rtsp_url,
            current_user.id,
            camera.id,
            create_alert
        ),
        daemon=True
    )

    thread.start()

    return {
        "message": "Caméra ajoutée",
        "camera_id": camera.id
    }

@router.delete("/{camera_id}")
def delete_camera(
    camera_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    camera = (
        db.query(models.Camera)
        .filter(
            models.Camera.id == camera_id,
            models.Camera.user_id == current_user.id
        )
        .first()
    )

    if not camera:
        raise HTTPException(
            status_code=404,
            detail="Caméra introuvable."
        )

    stop_camera_detection(camera_id)

    db.delete(camera)
    db.commit()

    return {
        "message": "Caméra supprimée",
        "camera_id": camera_id
    }

@router.put("/{camera_id}")
def update_camera(
    camera_id: int,
    data: dict = Body(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    camera = (
        db.query(models.Camera)
        .filter(
            models.Camera.id == camera_id,
            models.Camera.user_id == current_user.id
        )
        .first()
    )

    if not camera:
        raise HTTPException(
            status_code=404,
            detail="Caméra introuvable."
        )

    previous_rtsp_url = camera.rtsp_url

    if "camera_name" in data:
        camera.name = data["camera_name"]

    if "rtsp_url" in data:
        camera.rtsp_url = data["rtsp_url"]

    if "site_name" in data:
        camera.site_name = data["site_name"]

    if "location" in data:
        camera.location = data["location"]

    if "description" in data:
        camera.description = data["description"]

    previous_enabled = camera.is_enabled
    requested_enabled = data.get("is_enabled")

    rtsp_changed = (
        "rtsp_url" in data
        and data["rtsp_url"] != previous_rtsp_url
    )

    if (
        requested_enabled is not None
        and not isinstance(requested_enabled, bool)
    ):
        raise HTTPException(
            status_code=400,
            detail="is_enabled doit être un booléen."
        )

    if requested_enabled is not None:
        camera.is_enabled = requested_enabled

    db.commit()
    db.refresh(camera)

    if (
        requested_enabled is False
        and previous_enabled is True
    ):
        stop_camera_detection(camera.id)

    elif (
        requested_enabled is True
        and previous_enabled is False
    ):
        thread = threading.Thread(
            target=start_detection,
            args=(
                camera.rtsp_url,
                current_user.id,
                camera.id,
                create_alert
            ),
            daemon=True
        )

        thread.start()

    elif (
        rtsp_changed
        and camera.is_enabled is True
    ):
        stop_camera_detection(camera.id)

        stopped = wait_for_camera_detection_stop(
            camera.id,
            timeout=10
        )

        if not stopped:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Nouvelle URL RTSP enregistrée, mais "
                    "l'ancien moteur de détection ne s'est "
                    "pas arrêté dans le délai prévu. "
                    "Aucun second moteur n'a été lancé."
                )
            )

        thread = threading.Thread(
            target=start_detection,
            args=(
                camera.rtsp_url,
                current_user.id,
                camera.id,
                create_alert
            ),
            daemon=True
        )

        thread.start()

    return {
        "message": "Caméra modifiée",
        "camera_id": camera.id,
        "is_enabled": camera.is_enabled,
        "status": camera.status
    }
