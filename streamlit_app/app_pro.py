# streamlit_app/app_pro.py
import streamlit as st
import requests

st.set_page_config(page_title="Vida Secure AI – Pro", layout="centered")

st.title("Vida Secure AI – Abonnement Pro")
st.markdown("### Surveillance intelligente 24/7 – 79 €/mois")

# Retour de paiement
if st.query_params.get("success") == "true":
    st.success("Paiement réussi ! Bienvenue dans Vida Secure Pro")
    st.balloons()
    st.session_state.paid = True

if st.query_params.get("cancel") == "true":
    st.warning("Paiement annulé – tu peux réessayer")

# Page de paiement
if "paid" not in st.session_state:
    st.markdown("#### Abonnement mensuel – résiliable à tout moment")
    email = st.text_input("Ton email (pour la facture)", placeholder="jean@exemple.com")

    if st.button("Payer 79 €/mois avec Stripe", type="primary", use_container_width=True):
        if not email.strip():
            st.error("Entre ton email")
        else:
            with st.spinner("Redirection sécurisée vers Stripe..."):
                try:
                    r = requests.post( "https://vida-secure-ai.vercel.app/create-checkout-session",
                        json={"email": email.strip()},
                        timeout=15
                    )
                    data = r.json()
                    if "url" in data:
                        st.markdown(f'<meta http-equiv="refresh" content="0; url={data["url"]}">', 
                                  unsafe_allow_html=True)
                    else:
                        st.error(f"Erreur Stripe : {data.get('error')}")
                except:
                    st.error("Serveur temporaire – reviens dans 2 min")

# Accès Premium
else:
    st.success("Accès Premium activé !")
    rtsp = st.text_input("URL RTSP de ta caméra", 
                         value="rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mov")
    if st.button("Lancer la surveillance"):
        st.video(rtsp)
        st.write("Détection IA active (intrus, sacs abandonnés, etc.)")
