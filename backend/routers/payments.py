import os
import hmac
import hashlib
from datetime import datetime, timedelta

import requests
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

import models
from deps import get_db, get_current_user


router = APIRouter(
    tags=["Payments"]
)


PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")


def get_paystack_secret_key() -> str:
    if not PAYSTACK_SECRET_KEY:
        raise HTTPException(
            status_code=500,
            detail="Configuration Paystack absente"
        )

    return PAYSTACK_SECRET_KEY


@router.get("/payment-success")
def payment_success(
    reference: str,
    db: Session = Depends(get_db)
):
    secret_key = get_paystack_secret_key()

    url = (
        "https://api.paystack.co/transaction/verify/"
        f"{reference}"
    )

    headers = {
        "Authorization": f"Bearer {secret_key}"
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=15
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=502,
            detail="Impossible de vérifier le paiement auprès de Paystack"
        ) from exc

    transaction = data.get("data") or {}

    if transaction.get("status") != "success":
        return {"message": "Paiement échoué"}

    customer = transaction.get("customer") or {}
    email = customer.get("email")

    if not email:
        raise HTTPException(
            status_code=502,
            detail="Email client absent de la réponse Paystack"
        )

    user = (
        db.query(models.User)
        .filter(models.User.email == email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Utilisateur introuvable"
        )

    user.paid = True
    user.paid_until = datetime.utcnow() + timedelta(days=30)
    db.commit()

    return {"message": "Paiement validé"}


@router.post("/init-payment")
def init_payment(
    user: models.User = Depends(get_current_user)
):
    secret_key = get_paystack_secret_key()

    url = "https://api.paystack.co/transaction/initialize"

    headers = {
        "Authorization": f"Bearer {secret_key}",
        "Content-Type": "application/json"
    }

    data = {
        "email": user.email,
        "amount": 5000 * 100,
        "callback_url": "http://localhost:8501/?payment=success"
    }

    try:
        response = requests.post(
            url,
            json=data,
            headers=headers,
            timeout=15
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=502,
            detail="Impossible d'initialiser le paiement auprès de Paystack"
        ) from exc


@router.post("/paystack/webhook")
async def paystack_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    secret_key = get_paystack_secret_key()

    payload = await request.body()

    signature = request.headers.get(
        "x-paystack-signature"
    )

    computed_signature = hmac.new(
        secret_key.encode(),
        payload,
        hashlib.sha512
    ).hexdigest()

    if not signature or not hmac.compare_digest(
        signature,
        computed_signature
    ):
        raise HTTPException(
            status_code=400,
            detail="Signature invalide"
        )

    event = await request.json()

    if event.get("event") == "charge.success":
        event_data = event.get("data") or {}
        customer = event_data.get("customer") or {}
        email = customer.get("email")

        if email:
            user = (
                db.query(models.User)
                .filter(models.User.email == email)
                .first()
            )

            if user:
                user.paid = True
                user.paid_until = (
                    datetime.utcnow()
                    + timedelta(days=30)
                )
                db.commit()

                print(
                    f"PAIEMENT ACTIVE POUR : {email}"
                )

    return {"status": "success"}
