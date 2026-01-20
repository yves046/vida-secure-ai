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
# LYGOS – FACTURE
# =========================
def creer_paiement_lygos(montant, description="Abonnement Pro"):
    url = "https://api.lygosapp.com/v1/checkout"
    headers = {
        "Authorization": f"Bearer {os.environ.get('LYGOS_PRIVATE_KEY')}",
        "Content-Type": "application/json"
    }
    payload = {
        "amount": montant * 100,  # en centimes
        "currency": "XOF",
        "description": description,
        "return_url": "https://vida-secure-ai-7enddksqy2c8zpeeudblth.streamlit.app/?success=true",
        "cancel_url": "https://vida-secure-ai-7enddksqy2c8zpeeudblth.streamlit.app/?cancel=true",
        "customer_email": email
    }
    response = requests.post(url, json=payload, headers=headers, timeout=20)
    try:
        data = response.json()
        if data.get("status") == "success":
            return data["payment_url"]
        else:
            st.error("Erreur Lygos")
            st.write(data)
            return None
    except:
        st.error("Réponse Lygos invalide")
        return None

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

    # 🟠 Lygos (Mobile Money)
if st.button("Payer avec Wave / Orange / MTN (Lygos)", use_container_width=True):
    with st.spinner("Redirection vers Lygos..."):
        payment_url = creer_paiement_lygos(79)
        if payment_url:
            st.markdown(f'<meta http-equiv="refresh" content="0; url={payment_url}">', unsafe_allow_html=True)
        else:
            st.error("Erreur paiement Lygos")

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
