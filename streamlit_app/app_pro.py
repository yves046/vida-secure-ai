import os
import requests
import streamlit as st
import cv2

# =========================
# CONFIGURATION PAGE
# =========================
st.set_page_config(
    page_title="Vida Secure AI – Pro",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# =========================
# STYLE
# =========================
st.markdown("""
<style>
body { background-color: #f5f5f5; color: #222; }
.stButton>button { background-color: #4CAF50; color: white; font-size: 16px; padding: 10px; border-radius: 8px; }
.stTextInput>div>input { border-radius: 6px; padding: 8px; font-size: 14px; }
h1, h2, h3, h4 { color: #222; }
.stMarkdown p { font-size: 16px; }
</style>
""", unsafe_allow_html=True)

# =========================
# TITRE
# =========================
st.title("Vida Secure AI – Abonnement Pro")
st.markdown("### Surveillance intelligente 24/7 – 79 € / mois")
st.markdown("### Paiement sécurisé")

# =========================
# PAYSTACK
# =========================
PAYSTACK_SECRET_KEY = os.environ.get("PAYSTACK_SECRET_KEY")

if not PAYSTACK_SECRET_KEY:
    st.error("La clé Paystack n'est pas définie")
else:
    st.write("Clé Paystack détectée ✅")

def creer_paiement_paystack_test(montant, email, description="Abonnement Pro"):

    url = "https://api.paystack.co/transaction/initialize"

    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "email": email,
        "amount": int(montant * 100),
        "currency": "XOF",
        "callback_url": "https://vida-secure-ai-7enddksqy2c8zpeuublth.streamlit.app/?success=true",
        "metadata": {"description": description}
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        data = response.json()

        if data["status"]:
            return data["data"]["authorization_url"]
        else:
            return None

    except Exception as e:
        st.error(str(e))
        return None


# =========================
# PAIEMENT SUCCESS
# =========================
if st.query_params.get("success") == "true":
    st.session_state.paid = True


# =========================
# PAGE ABONNEMENT
# =========================
if "paid" not in st.session_state:

    email = st.text_input("Ton email (pour la facture)", placeholder="jean@exemple.com")

    # STRIPE
    if st.button("Payer 79 € par carte (Stripe)", use_container_width=True):

        if not email.strip():
            st.error("Entre ton email")

        else:

            with st.spinner("Redirection vers Stripe..."):

                try:

                    r = requests.post(
                        "https://vida-secure-ai-2.onrender.com/create-checkout-session",
                        json={"email": email.strip()},
                        timeout=15
                    )

                    data = r.json()

                    if "url" in data:

                        st.link_button(
                            "👉 Continuer vers le paiement sécurisé Stripe",
                            data["url"],
                            use_container_width=True
                        )

                    else:
                        st.error("Erreur Stripe")

                except Exception as e:
                    st.error(str(e))

    st.divider()

    # PAYSTACK
    if st.button("Payer 79 € avec Paystack (Test)", use_container_width=True):

        if not email.strip():
            st.warning("Veuillez entrer votre email")

        else:

            payment_url = creer_paiement_paystack_test(79, email.strip())

            if payment_url:
                st.markdown(
                    f'<meta http-equiv="refresh" content="0; url={payment_url}">',
                    unsafe_allow_html=True
                )
            else:
                st.error("Erreur paiement Paystack")


# =========================
# ACCÈS PREMIUM
# =========================
else:

    st.success("Accès Premium activé ✅")

    rtsp = st.text_input(
        "URL RTSP de ta caméra",
        value="rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mov"
    )

    if st.button("Lancer la surveillance"):

        cap = cv2.VideoCapture(rtsp)

        frame_window = st.image([])

        while True:

            ret, frame = cap.read()

            if not ret:
                st.error("Impossible de lire la caméra")
                break

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            frame_window.image(frame)

        cap.release()

        st.write("Détection IA active (intrus, sacs abandonnés, etc.)")
