from datetime import datetime, timedelta
from fastapi import APIRouter, Form, Depends, HTTPException
from sqlalchemy.orm import Session

import models

from deps import get_db, get_current_user
from security import (
    hash_password,
    verify_password,
    create_access_token,
)



router = APIRouter(
    tags=["Authentication"]
)


@router.post("/register")
def register(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = (
        db.query(models.User)
        .filter(models.User.email == email)
        .first()
    )

    if user is not None:
        raise HTTPException(
            status_code=400,
            detail="Email déjà utilisé"
        )

    trial_start = datetime.utcnow()

    new_user = models.User(
        email=email,
        password_hash=hash_password(password),
        paid=False,
        trial_started_at=trial_start,
        trial_until=trial_start + timedelta(days=7)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "Utilisateur créé",
        "trial_days": 7,
        "trial_until": new_user.trial_until.isoformat()
    }


@router.post("/login")
def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    email = username

    user = (
        db.query(models.User)
        .filter(models.User.email == email)
        .first()
    )

    if not user or not verify_password(
        password,
        user.password_hash
    ):
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

@router.get("/me")
def get_me(
    current_user: models.User = Depends(get_current_user)
):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "paid": current_user.paid,
        "paid_until": (
            current_user.paid_until.isoformat()
            if current_user.paid_until
            else None
        ),
        "trial_started_at": (
            current_user.trial_started_at.isoformat()
            if current_user.trial_started_at
            else None
        ),
        "trial_until": (
            current_user.trial_until.isoformat()
            if current_user.trial_until
            else None
        )
    }
