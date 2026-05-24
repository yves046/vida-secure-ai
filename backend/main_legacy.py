from fastapi import FastAPI, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
import stripe
import uvicorn
import os
from datetime import datetime

app = FastAPI(title="Vida Secure AI – API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stripe (on mettra la vraie clé dans .env plus tard)
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_123")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/api/health")
def health():
    return {"status": "alive", "time": datetime.now().isoformat()}

@app.post("/api/upload-rtsp")
async def add_camera(rtsp_url: str = Form(...), user_id: str = "demo"):
    cam_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(f"logs/{cam_id}", exist_ok=True)
    with open(f"logs/{cam_id}/rtsp.txt", "w") as f:
        f.write(rtsp_url)
    return {"cam_id": cam_id, "status": "active", "message": "Caméra ajoutée avec succès"}
from fastapi import Request
from dotenv import load_dotenv
load_dotenv()

import stripe
from fastapi import Request
from dotenv import load_dotenv
import os

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

@app.post("/create-checkout-session")
async def create_checkout_session():
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': STRIPE_PRICE_ID,
                'quantity': 1,
            }],
            mode='subscription',
            success_url='http://127.0.0.1:8501/?success=true',
            cancel_url='http://127.0.0.1:8501/?cancel=true',
        )
        return {"url": session.url}
    except Exception as e:
        return {"error": str(e)}