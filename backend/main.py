from backend.models import Alert
from backend.database import SessionLocal
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Form, HTTPException, Depends, Body, BackgroundTasks, Request
from database import engine, SessionLocal
from fastapi.responses import FileResponse
from backend.models import Base, User, Alert
from sqlalchemy.orm import Session
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from backend.intrusion import start_detection
import backend.models as models
import threading
import os
import requests
import hmac
import hashlib


from backend.database import engine
from backend.security import hash_password, verify_password, create_access_token
from backend.deps import get_db, get_current_user
from datetime import timedelta

models.Base.metadata.create_all(bind=engine)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PAYSTACK_SECRET_KEY = "sk_test_0483a422773bd7c816e5e06b2008109279501ac1"

app = FastAPI()
app.mount(
    "/videos",
    StaticFiles(directory=os.path.join(BASE_DIR, "videos")),
    name="videos"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================== ROUTES AUTH =====================
@app.post("/register")
def register(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()

    if user is not None:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")

    new_user = models.User(
        email=email,
        password_hash=hash_password(password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "Utilisateur créé"}


@app.post("/login")
def login(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Identifiants invalides")
    
    token = create_access_token({"sub": str(user.id)})

    return {
        "access_token": token,
        "token_type": "bearer"
    }

@app.post("/test-alert")
def test_alert(
    data: dict,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    alert = models.Alert(
        user_id=user.id,
        message=data.get("message"),
        video_url=data.get("video_url"),
        timestamp=datetime.utcnow()
    )

    db.add(alert)
    db.commit()

    return {"status": "saved"}

@app.get("/dashboard")
def dashboard(user: models.User = Depends(get_current_user)):
    return {"message": "Bienvenue !", "email": user.email}


@app.get("/stats")
def get_stats(
    user: models.User = Depends(get_current_user)
):

    return {
        "email": user.email,
        "paid": user.paid
    }


@app.get("/alerts")
def get_alerts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    
    # 🔒 Vérification abonnement
    if not current_user.paid:
        raise HTTPException(status_code=403, detail="Abonnement requis")

    alerts = db.query(models.Alert)\
        .filter(models.Alert.user_id == current_user.id)\
        .order_by(models.Alert.timestamp.desc())\
        .all()

    return [
        {
            "id": a.id,
            "message": a.message,
            "video_url": f"http://127.0.0.1:8000/secure-video/{a.video_url}",
            "timestamp": a.timestamp
        }
        for a in alerts
    ]

@app.get("/payment-success")
def payment_success(reference: str, db: Session = Depends(get_db)):
    url = f"https://api.paystack.co/transaction/verify/{reference}"

    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"
    }

    response = requests.get(url, headers=headers)
    data = response.json()

    if data["data"]["status"] == "success":
        email = data["data"]["customer"]["email"]

        user = db.query(models.User).filter(models.User.email == email).first()

        if user:
            user.paid = True
            user.paid_until = datetime.utcnow() + timedelta(days=30)
            db.commit()

        return {"message": "Paiement validé"}

    return {"message": "Paiement échoué"}

@app.get("/activate-payment")
def activate_payment(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    user.paid = True
    db.commit()
    return {"message": "Paiement activé"}

@app.get("/payment-success")
def payment_success():
    return {"message": "Paiement reçu avec succès"}

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

# ===================== TEST ALERT (photo + vidéo + PDF) =====================
@app.post("/test-alert")
def test_alert():
    user = db.query(User).first()  # ou ton vrai filtre

    if not user:
        return {"error": "User non trouvé"}

    if not user.paid:
        return {"error": "Utilisateur non abonné"}

    return {"message": "Alerte envoyée"}

def send_alert_email(to_email: str, photo_path: str, clip_path: str, pdf_path: str, timestamp: str):
    msg = MIMEMultipart()
    msg["From"] = os.getenv("EMAIL_USER")
    msg["To"] = to_email
    msg["Subject"] = f"Alerte Intrusion - {timestamp}"

    body = f"Alerte intrusion détectée à {timestamp}\n\nFichiers joints :"
    msg.attach(MIMEText(body, "plain"))

    # Photo
    if os.path.exists(photo_path):
        with open(photo_path, "rb") as f:
            msg.attach(MIMEImage(f.read(), name=f"photo_{timestamp}.jpg"))

    # Clip
    if os.path.exists(clip_path):
        with open(clip_path, "rb") as f:
            part = MIMEApplication(f.read(), _subtype="mp4")
            part.add_header("Content-Disposition", "attachment", filename=f"clip_{timestamp}.mp4")
            msg.attach(part)

    # PDF
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            part = MIMEApplication(f.read(), _subtype="pdf")
            part.add_header("Content-Disposition", "attachment", filename=f"report_{timestamp}.pdf")
            msg.attach(part)

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASSWORD"))
        server.send_message(msg)
        server.quit()
        print(f"Email envoyé à {to_email}")
    except Exception as e:
        print(f"Erreur email: {e}")

@app.post("/init-payment")
def init_payment(user: models.User = Depends(get_current_user)):
    url = "https://api.paystack.co/transaction/initialize"
    
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
            
    data = {
        "email": user.email,
        "amount": 5000 * 100,
        "callback_url": "http://localhost:8501/?payment=success"
    }
            
    response = requests.post(url, json=data, headers=headers)

    print("PAYSTACK RESPONSE:", response.text)  # 🔴 debug

    return response.json()

@app.post("/paystack/webhook")
async def paystack_webhook(
    request: Request,
    db: Session = Depends(get_db)
):

    payload = await request.body()

    signature = request.headers.get("x-paystack-signature")

    computed_signature = hmac.new(
        PAYSTACK_SECRET_KEY.encode(),
        payload,
        hashlib.sha512
    ).hexdigest()

    if signature != computed_signature:
        raise HTTPException(
            status_code=400,
            detail="Signature invalide"
        )

    event = await request.json()

    if event["event"] == "charge.success":

        email = event["data"]["customer"]["email"]

        user = db.query(models.User).filter(
            models.User.email == email
        ).first()

        if user:

            user.paid = True

            db.commit()

            print(f"PAIEMENT ACTIVE POUR : {email}")

    return {"status": "success"}

@app.on_event("startup")
def start_camera():
    thread = threading.Thread(
        target=start_detection,
        args=("rtsp://Yves040:Yves46839488@10.10.10.33:554/stream1", create_alert)
    )
    thread.daemon = True
    thread.start()

def create_alert(video_filename):
    db = SessionLocal()

    new_alert = Alert(
        user_id=1,  # ⚠️ mets un user existant en base
        message="Intrusion détectée",
        video_url=video_filename
    )

    db.add(new_alert)
    db.commit()
    db.close()
