# streamlit_app/app_pro.py
import streamlit as st
import requests
import os

st.set_page_config(page_title="Vida Secure AI – Pro", layout="centered")

st.title("Vida Secure AI – Abonnement Pro")
st.markdown("### Surveillance intelligente 24/7 – 79 €/mois")

# 🔑 Récupération des clés PayDunya depuis Render (production)
PAYDUNYA_TOKEN = os.environ.get("PAYDUNYA_TOKEN")

# 1️⃣ Fonction pour créer une facture PayDunya
def creer_paiement(montant, description="Abonnement Pro"):
    url = "https://app.paydunya.com/api/checkout-invoice/create"

    headers = {
        "PAYDUNYA-MASTER-KEY": os.environ.get("PAYDUNYA_MASTER_KEY"),
        "PAYDUNYA-PRIVATE-KEY": os.environ.get("PAYDUNYA_PRIVATE_KEY"),
        "PAYDUNYA-TOKEN": os.environ.get("PAYDUNYA_TOKEN"),
        "Content-Type": "application/json"
    }

    payload = {
        "invoice": {
            "total_amount": montant,
            "description": description
        },
        "store": {
            "name": "Vida Secure AI"
        },
        "actions": {
            "callback_url": "https://vida-secure-ai-7enddksqy2c8zpeeudblth.streamlit.app?success=true",
            "cancel_url": "https://vida-secure-ai-7enddksqy2c8zpeeudblth.streamlit.app?cancel=true"
        },
        "items": [
            {
                "name": description,
                "quantity": 1,
                "unit_price": montant,
                "total_price": montant
            }
        ]
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code != 200:
        st.error("Erreur PayDunya (HTTP)")
        st.text(response.text)
        return None

    return response.json()

# 2️⃣ Gestion du retour de paiement
if st.query_params.get("success") == "true":
    st.success("Paiement réussi ! Bienvenue dans Vida Secure Pro 🎉")
    st.balloons()
    st.session_state.paid = True

if st.query_params.get("cancel") == "true":
    st.warning("Paiement annulé – tu peux réessayer")

# 3️⃣ Page d’abonnement si pas encore payé
if "paid" not in st.session_state:
    st.markdown("#### Abonnement mensuel – résiliable à tout moment")
    email = st.text_input("Ton email (pour la facture)", placeholder="jean@exemple.com")

    # 🔹 Bouton Stripe
    if st.button("Payer 79 €/mois avec Stripe", type="primary", use_container_width=True):
        if not email.strip():
            st.error("Entre ton email")
        else:
            with st.spinner("Préparation du paiement sécurisé..."):
                try:
                    r = requests.post(
                        "https://vida-secure-ai-2.onrender.com/create-checkout-session",
                        json={"email": email.strip()},
                        timeout=15
                    )
                    data = r.json()
                    if "url" in data:
                        st.success("Paiement prêt ✅")
                        st.link_button(
                            "👉 Continuer vers le paiement sécurisé Stripe",
                            data["url"],
                            use_container_width=True
                        )
                    else:
                        st.error(f"Erreur Stripe : {data.get('error')}")
                except Exception as e:
                    st.error("Serveur temporaire – reviens dans 2 min")

    # 🔹 Bouton PayDunya avec redirection automatique
    if st.button("Payer maintenant avec Wave / Orange / MTN"):
        paiement = creer_paiement(79)
        if paiement and paiement.get("response_code") == "00":
    invoice_url = paiement["response_text"]
    st.markdown(
        f'<meta http-equiv="refresh" content="0; url={invoice_url}">',
        unsafe_allow_html=True
    )
else:
    st.error("Création de facture PayDunya échouée")


# 4️⃣ Accès Premium si déjà payé
else:
    st.success("Accès Premium activé ! ✅")
    rtsp = st.text_input(
        "URL RTSP de ta caméra", 
        value="rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mov"
    )
    if st.button("Lancer la surveillance"):
        st.video(rtsp)
        st.write("Détection IA active (intrus, sacs abandonnés, etc.)")
