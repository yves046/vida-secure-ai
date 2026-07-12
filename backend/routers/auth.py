from fastapi import APIRouter, Form, Depends, HTTPException
from sqlalchemy.orm import Session

import models

from deps import get_db
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

    new_user = models.User(
        email=email,
        password_hash=hash_password(password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "Utilisateur créé"
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
