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

# Style CSS
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
# PAYDUNYA – FACTURE
# =========================
def creer_paiement_paydunya(montant, description="Abonnement Pro"):
    url = "https://api.paydunya.com/api/checkout-invoice/create"

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "PAYDUNYA-MASTER-KEY": os.getenv("PAYDUNYA_MASTER_KEY"),
        "PAYDUNYA-PRIVATE-KEY": os.getenv("PAYDUNYA_PRIVATE_KEY"),
        "PAYDUNYA-TOKEN": os.getenv("PAYDUNYA_TOKEN"),
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

    response = requests.post(url, json=payload, headers=headers, timeout=20)

    try:
        data = response.json()
    except Exception:
        st.error("Réponse PayDunya non JSON (URL ou headers incorrects)")
        st.code(response.text)
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

    # 🔵 Stripe
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
                    st.link_button("👉 Continuer vers le paiement sécurisé Stripe", data["url"], use_container_width=True)
                else:
                    st.error("Erreur Stripe")

    st.divider()

    # 🟠 PayDunya
    if st.button("Payer avec Wave / Orange / MTN", use_container_width=True):
        with st.spinner("Redirection vers PayDunya..."):
            paiement = creer_paiement_paydunya(50000)
            if paiement and paiement.get("response_code") == "00":
                invoice_url = paiement["checkout_url"]
st.link_button("👉 Continuer vers le paiement PayDunya", invoice_url, use_container_width=True)
                st.markdown(f'<meta http-equiv="refresh" content="0; url={invoice_url}">', unsafe_allow_html=True)
            else:
                st.error("Erreur lors de la création du paiement PayDunya")

    st.divider()
     
     if st.button("Tester paiement PayDunya"):
    result = creer_paiement_paydunya(1000)

    if result:
        st.success("Facture créée avec succès")
        st.write(result)
        st.markdown(f"[Payer ici]({result['invoice_url']})")

    # 🔴 Paiement hors ligne
    if st.button("Paiement hors ligne (liquide ou RDV sur place)", use_container_width=True, type="primary"):
        st.info("Remplis ce formulaire → je te contacte sous 24h pour le RDV et l'activation immédiate.")
        name = st.text_input("Nom du magasin ou de la personne")
        address = st.text_input("Adresse du magasin")
        phone = st.text_input("Ton numéro de téléphone (WhatsApp de préférence)")
        cams = st.number_input("Nombre de caméras", min_value=1, max_value=20, value=4)
        
     
