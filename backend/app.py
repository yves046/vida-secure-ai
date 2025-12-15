from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import stripe
import os

app = FastAPI()

# Autoriser ton frontend Streamlit à appeler l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Clé Stripe depuis Render environment variables
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

@app.post("/create-checkout-session")
async def create_checkout_session(req: Request):
    data = await req.json()
    email = data.get("email")
    if not email:
        return {"error": "Email manquant"}

    try:
    session = stripe.checkout.Session.create(
        customer_email=email,
        line_items=[{"price": "ton_price_id", "quantity": 1}],
        mode="subscription",
        success_url="https://ton-site/success",
        cancel_url="https://ton-site/cancel"
    )
except Exception as e:
    return {"error": str(e)}
