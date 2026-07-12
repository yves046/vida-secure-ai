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

    return {
        "cameras": 1,
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
            "image": row["image_path"],
            "video": row["video_path"],
            "pdf": row["pdf_path"]
        }
        for row in incidents
    ]
