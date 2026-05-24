import streamlit as st
import requests

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Vida Secure AI", layout="centered")

st.title("VIDA Secure AI")
st.subheader("Surveillance intelligente")

# =========================
# EMAIL CLIENT
# =========================
email = st.text_input("Ton email")

# =========================
# ACCÈS (simulation paiement OK)
# =========================
if email:

    st.success("Accès activé ✅")

    # ------------------------
    # AJOUT CAMERA
    # ------------------------
    st.subheader("Ajouter une caméra")

    camera_name = st.text_input("Nom de la caméra", placeholder="Entrée principale")
    rtsp = st.text_input("URL RTSP")

    if st.button("Ajouter caméra"):

        if not camera_name or not rtsp:
            st.warning("Remplis tous les champs")
        else:
            try:
                r = requests.post(
                    "http://127.0.0.1:5000/add-camera",
                    json={
                        "email": email,
                        "rtsp": rtsp,
                        "name": camera_name
                    }
                )

                if r.status_code == 200:
                    st.success("Caméra ajoutée ✅")
                else:
                    st.error("Erreur backend")

            except Exception as e:
                st.error(str(e))