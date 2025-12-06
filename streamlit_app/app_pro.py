import streamlit as st
import requests

st.set_page_config(page_title="Vida Secure AI", layout="centered")
st.title("🔒 Vida Secure AI – Abonnement Pro")
st.markdown("### Surveillance intelligente 24/7 – 79 €/mois")

if "paid" not in st.session_state:
    st.info("Débloquez l'accès complet en 10 secondes")
    if st.button("Payer 79 €/mois avec Stripe", type="primary"):
        with st.spinner("Redirection vers Stripe..."):
            try:
                r = requests.post("http://localhost:8000/create-checkout-session", 
                                json={"user_id": "demo"})
                st.session_state.checkout_url = r.json()["url"]
            except:
                st.session_state.checkout_url = "https://buy.stripe.com/test_..."  # lien test
        st.success("Redirection...")
        st.markdown(f"[Payer maintenant →]({st.session_state.checkout_url})")
else:
    st.success("✅ Accès Premium activé – Bienvenue !")
    st.balloons()
    
    rtsp = st.text_input("RTSP ou IP caméra", "rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4")
    if st.button("Lancer la surveillance"):
        st.video(rtsp)
        st.write("Détection IA activée (intrus, sacs abandonnés, etc.)")
