import os
import requests
import streamlit as st

st.set_page_config(page_title="Vida Secure AI – Pro", layout="centered")

# =========================
# FONCTION PAYDUNYA
# =========================
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
            "callback_url": "https://vida-secure-ai-7enddksqy2c8zpeeudblth.streamlit.app/?success=true",
            "cancel_url": "https://vida-secure-ai-7enddksqy2c8zpeeudblth.streamlit.app/?cancel=true"
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

    response = requests.post(url, json=payload, headers=headers, timeout=20)

    if response.status_code != 200:
        return None

    return response.json()

# =========================
# INTERFACE
# =========================
st.title("Vida Secure AI – Abonnement Pro")
st.markdown("### Surveillance intelligente 24/7 – 79 € / mois")

if "paid" not in st.session_state:

    if st.query_params.get("success") == "true":
        st.success("Paiement réussi 🎉")
        st.session_state.paid = True

    if st.query_params.get("cancel") == "true":
        st.warning("Paiement annulé")

    st.markdown("#### Paiement sécurisé")
    if st.button("Payer avec Wave / Orange / MTN", use_container_width=True):
        with st.spinner("Redirection vers PayDunya..."):
            paiement = creer_paiement(79)

            if paiement and paiement.get("response_code") == "00":
                invoice_url = paiement["response_text"]
                st.markdown(
                    f'<meta http-equiv="refresh" content="0; url={invoice_url}">',
                    unsafe_allow_html=True
                )
            else:
                st.error("Erreur lors de la création du paiement PayDunya")

else:
    st.success("Accès Premium activé ✅")
    st.text("Merci pour votre abonnement !")
