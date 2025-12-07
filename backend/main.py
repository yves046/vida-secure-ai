# backend/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import stripe
import os

# === Création de l'app FastAPI ===
app = FastAPI(title="Vida Secure AI – Backend")

# === CORS : autorise Streamlit (local + déployé) à appeler le backend ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],                    # En prod tu peux restreindre, mais pour le sprint → "*"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Clé secrète Stripe (prise dans les variables d’environnement) ===
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
if not stripe.api_key:
    raise RuntimeError("Variable d’environnement STRIPE_SECRET_KEY manquante !")

# === ID du prix que tu vas créer dans le Dashboard Stripe (79 €/mois récurrent) ===
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID", "price_123456789")  # tu le changeras dans 2 minutes

# === Endpoint qui crée la session de paiement Stripe ===
@app.post("/create-checkout-session")
async def create_checkout_session(request: Request):
    try:
        data = await request.json()
        email = data.get("email", "").strip()

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            customer_email=email if email else None,
            line_items=[
                {
                    "price": STRIPE_PRICE_ID,
                    "quantity": 1,
                }
            ],
            mode="subscription",   # abonnement mensuel
            success_url="https://vida-secure-ai-7enddksqy2c8zpeeudblth.streamlit.app/?success=true",
            cancel_url="https://vida-secure-ai-7enddksqy2c8zpeeudblth.streamlit.app/?cancel=true",
            metadata={"source": "vida-secure-ai"},
        )
        return {"url": session.url}

    except Exception as e:
        return {"error": str(e)}

# === Pour tester que le backend tourne bien ===
@app.get("/api/health")
def health():
    return {"status": "alive", "time": __import__('datetime').datetime.now().isoformat()}
