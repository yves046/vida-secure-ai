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
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "eur",
                    "product_data": {"name": "Vida Secure AI – Abonnement Pro"},
                    "unit_amount": 7900,  # 79 € en centimes
                },
                "quantity": 1,
            }],
            mode="subscription",
            success_url="https://ton-frontend-streamlit.com/?success=true",
            cancel_url="https://ton-frontend-streamlit.com/?cancel=true",
            customer_email=email
        )
        return {"url": session.url}
    except Exception as e:
        return {"error": str(e)}
