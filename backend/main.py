from flask import Flask, request, jsonify
import stripe
import os

app = Flask(__name__)

# Clé Stripe (depuis les variables d'environnement)
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
PAYDUNYA_MASTER_KEY = os.getenv("PAYDUNYA_MASTER_KEY")
PAYDUNYA_PUBLIC_KEY = os.getenv("PAYDUNYA_PUBLIC_KEY")
PAYDUNYA_PRIVATE_KEY = os.getenv("PAYDUNYA_PRIVATE_KEY")
PAYDUNYA_TOKEN = os.getenv("PAYDUNYA_TOKEN")

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    data = request.get_json()
    email = data.get("email")
    if not email:
        return jsonify({"error": "Email manquant"}), 400

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
            success_url="http://localhost:8501/?success=true",
            cancel_url="http://localhost:8501/?cancel=true",
            customer_email=email
        )
        return jsonify({"url": session.url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
import requests
from fastapi import FastAPI

app = FastAPI()

@app.post("/create-payment")
def create_payment():
    url = "https://app.paydunya.com/api/v1/checkout-invoice/create"

    headers = {
        "Content-Type": "application/json",
        "PAYDUNYA-MASTER-KEY": PAYDUNYA_MASTER_KEY,
        "PAYDUNYA-PRIVATE-KEY": PAYDUNYA_PRIVATE_KEY,
        "PAYDUNYA-TOKEN": PAYDUNYA_TOKEN
    }

    payload = {
        "invoice": {
            "total_amount": 79,
            "description": "Abonnement Vida Secure AI - 1 mois"
        },
        "store": {
            "name": "Vida Secure AI"
        },
        "actions": {
            "callback_url": "https://TON-BACKEND.onrender.com/payment-callback",
            "return_url": "https://TON-SITE.streamlit.app/success",
            "cancel_url": "https://TON-SITE.streamlit.app/cancel"
        }
    }
