import os
import requests
import streamlit as st

# =========================
# CONFIGURATION PAGE
# =========================
st.set_page_config(
    page_title="Vida Secure AI – Pro",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Style CSS pour fond clair et look pro
st.markdown("""
<style>
body {
    background-color: #f5f5f5;
    color: #222;
}
.stButton>button {
    background-color: #4CAF50;
    color: white;
    font-size: 16px;
    padding: 10px;
    border-radius: 8px;
}
.stTextInput>div>input {
    border-radius: 6px;
    padding: 8px;
    font-size: 14px;
}
h1, h2, h3, h4 {
    color: #222;
}
.stMarkdown p {
    font-size: 16px;
}
</style>
""", unsafe_allow_html=True)

# =========================
# TITRE
# =========================
st.title("Vida Secure AI – Abonnement Pro")
st.markdown("### Surveillance intelligente 24/7 – 79 € / mois")
st.markdown("### Paiement sécurisé")

# =========================
# PAYDUNYA – FACTURE
# =========================
def creer_paiement_paydunya(montant, description="Abonnement Pro"):
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
            "description": "Abonnement Vida Secure AI pro"
        },
        "store": {
            "name": "Vida Secure AI"
        },
        "actions": {
            "callback_url": "https://vida-secure-ai-7enddksqy2c8zpeeudblth.streamlit.app/?success=true",
            "cancel_url": "https://vida-secure-ai-7enddksqy2c8zpeeudblth.streamlit.app/?cancel=true"
        }
    }

    response = requests.post(url, json=payload, headers=headers)
    
    try:
        return response.json()
    except:
        st.error("PayDunna a envoyé une page HTML (mauvaise config)")
        st.text(response.text)
        return {}

# =========================
# RETOUR PAIEMENT
# =========================
if st.query_params.get("success") == "true":
    st.success("Paiement réussi 🎉 Bienvenue dans Vida Secure Pro")
    st.session_state.paid = True

if st.query_params.get("cancel") == "true":
    st.warning("Paiement annulé")

# =========================
# PAGE ABONNEMENT
# =========================
if "paid" not in st.session_state:
    email = st.text_input("Ton email (pour la facture)", placeholder="jean@exemple.com")

    # 🔵 Stripe (carte bancaire)
    if st.button("Payer 79 € par carte (Stripe)", use_container_width=True):
        if not email.strip():
            st.error("Entre ton email")
        else:
            with st.spinner("Redirection vers Stripe..."):
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

    st.divider()

    # 🟠 PayDunya (Mobile Money)
    if st.button("Payer avec Wave / Orange / MTN", use_container_width=True):
        with st.spinner("Redirection vers PayDunya..."):
            paiement = creer_paiement_paydunya(79)
            if paiement and paiement.get("response_code") == "00":
                invoice_url = paiement["response_text"]
                st.markdown(
                    f'<meta http-equiv="refresh" content="0; url={invoice_url}">',
                    unsafe_allow_html=True
                )
            else:
                st.error("Erreur lors de la création du paiement PayDunya")

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
        st.video(rtsp)
        st.write("Détection IA active (intrus, sacs abandonnés, etc.)")
