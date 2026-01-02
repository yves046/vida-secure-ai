# =========================
# VIDA SECURE AI – PAIEMENTS STREAMLIT
# =========================

import os
import requests
import stripe
import streamlit as st

# =========================
# CONFIGURATION PAYDUNYA
# =========================
PAYDUNYA_MASTER_KEY = os.getenv("PAYDUNYA_MASTER_KEY")
PAYDUNYA_PRIVATE_KEY = os.getenv("PAYDUNYA_PRIVATE_KEY")
PAYDUNYA_TOKEN = os.getenv("PAYDUNYA_TOKEN")
PAYDUNYA_URL = "https://api.paydunya.com/api/checkout-invoice/create"

# =========================
# CONFIGURATION STRIPE
# =========================
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
stripe.api_key = STRIPE_SECRET_KEY

# =========================
# FONCTION PAYDUNYA
# =========================
def creer_paiement_paydunya(montant, description="Abonnement Pro"):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "PAYDUNYA-MASTER-KEY": PAYDUNYA_MASTER_KEY,
        "PAYDUNYA-PRIVATE-KEY": PAYDUNYA_PRIVATE_KEY,
        "PAYDUNYA-TOKEN": PAYDUNYA_TOKEN
    }

    payload = {
        "invoice": {
            "total_amount": int(montant),
            "description": description
        },
        "store": {
            "name": "Vida Secure AI"
        },
        "actions": {
            "callback_url": "https://vida-secure-ai-7enddksqy2c8zpeeudblth.streamlit.app",
            "cancel_url": "https://vida-secure-ai-7enddksqy2c8zpeeudblth.streamlit.app"
        }
    }

    try:
        response = requests.post(PAYDUNYA_URL, headers=headers, json=payload, timeout=20)
        data = response.json()
    except Exception as e:
        st.error("Erreur lors de l'appel à PayDunya")
        st.code(str(e))
        return None

    if response.status_code != 200:
        st.error(f"Erreur HTTP PayDunya : {response.status_code}")
        st.code(data)
        return None

    if data.get("response_code") != "00":
        st.error("PayDunya a refusé la requête")
        st.code(data)
        return None

    return data

# =========================
# FONCTION STRIPE
# =========================
def creer_paiement_stripe(montant, description="Abonnement Pro"):
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": description,
                    },
                    "unit_amount": int(montant * 100),  # Stripe en cents
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url="https://vida-secure-ai-7enddksqy2c8zpeeudblth.streamlit.app/?success=true",
            cancel_url="https://vida-secure-ai-7enddksqy2c8zpeeudblth.streamlit.app/?cancel=true",
        )
        return session
    except Exception as e:
        st.error("Erreur lors de l'appel à Stripe")
        st.code(str(e))
        return None

# =========================
# STREAMLIT UI
# =========================
st.title("Paiement Vida Secure AI")

montant = st.number_input("Montant à payer", min_value=100, value=1000, step=100)
mode = st.radio("Mode de paiement", ["PayDunya", "Stripe"])

if st.button("Payer maintenant"):
    if mode == "PayDunya":
        resultat = creer_paiement_paydunya(montant)
        if resultat:
            st.success("Facture PayDunya créée !")
            st.write(resultat)
            st.markdown(f"[Payer ici]({resultat['invoice_url']})")
    else:
        session = creer_paiement_stripe(montant)
        if session:
            st.success("Session Stripe créée !")
            st.markdown(f"[Payer ici via Stripe]({session.url})")
