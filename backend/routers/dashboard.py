import os
import sqlite3

from fastapi import APIRouter, Depends, HTTPException

import models
from deps import get_current_user


router = APIRouter(
    tags=["Dashboard"]
)


@router.get("/dashboard")
def dashboard(
    user: models.User = Depends(get_current_user)
):
    print("========== USER CONNECTÉ ==========")
    print("ID :", user.id)
    print("EMAIL :", user.email)
    print("PAID :", user.paid)
    print("===================================")

    return {
        "message": "Bienvenue !",
        "email": user.email
    }


@router.get("/stats")
def get_stats(
    user: models.User = Depends(get_current_user)
):
    conn = sqlite3.connect("vida_incidents.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM incidents
        WHERE user_id = ?
        """,
        (user.id,)
    )

    total_alerts = cursor.fetchone()[0]

    conn.close()

    from database import SessionLocal
    from models import Camera

    db = SessionLocal()

    try:
        total_cameras = (
            db.query(Camera)
            .filter(Camera.user_id == user.id)
            .count()
        )
    finally:
        db.close()

    return {
        "cameras": total_cameras,
        "alerts": total_alerts,
        "status": "ACTIVE",
        "paid": user.paid
    }


@router.get("/alerts")
def get_alerts(
    current_user: models.User = Depends(get_current_user)
):
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

    cursor.execute(
        """
        SELECT *
        FROM incidents
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 20
        """,
        (current_user.id,)
    )

    incidents = cursor.fetchall()

    conn.close()

    return [
        {
            "id": row["incident_id"],
            "type": row["alert_level"],
            "zone": row["zone_name"],
            "persons": row["persons_count"],
            "timestamp": row["timestamp"],
            "image": (
                f"/secure-image/{os.path.basename(row['image_path'])}"
                if row["image_path"]
                else None
            ),
            "video": (
                f"/secure-video/{os.path.basename(row['video_path'])}"
                if row["video_path"]
                else None
            ),
            "pdf": (
                f"/secure-pdf/{os.path.basename(row['pdf_path'])}"
                if row["pdf_path"]
                else None
            )
        }
        for row in incidents
    ]
