import streamlit as st
import requests

st.title("Paiement Stripe Test")

if st.button("Payer avec Stripe"):
    try:
        # Envoie POST vers ton backend Render
        response = requests.post(
            "https://vida-secure-ai.onrender.com/create-checkout-session",
            json={"email": "test@example.com"}  # ou email de l'utilisateur
        )
        if response.status_code == 200 and "url" in response.json():
            checkout_url = response.json()["url"]
            # Affiche le lien cliquable pour payer
            st.markdown(f"[Clique ici pour payer]({checkout_url})")
        else:
            st.error(f"Erreur serveur : {response.json()}")
    except Exception as e:
        st.error(f"Erreur : {e}")

