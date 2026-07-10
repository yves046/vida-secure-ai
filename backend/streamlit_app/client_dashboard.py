import streamlit as st
import cv2
import threading
import queue
import json
import requests
import time
from ultralytics import YOLO
from PIL import Image, ImageDraw

from components.sidebar import render_sidebar
from components.camera_card import render_camera_card

# -----------------
# Configuration page
# -----------------
st.set_page_config(page_title="Vida Secure AI Pro", layout="wide")

st.markdown("""
<style>
    .css-1d391kg {background-color: #0e1117;}
    .css-1v0mbdj {color: #ffffff;}
    h1 {color: #ff4b4b; text-align: center;}
</style>
""", unsafe_allow_html=True)

# -----------------
# Backend URL
# -----------------
API_URL = "http://127.0.0.1:8000"

# -----------------
# Chargement du modèle IA
# -----------------
model = YOLO("yolov8n.pt")

# -----------------
# Auth
# -----------------
if "token" not in st.session_state:
    st.session_state.token = None

if "email" not in st.session_state:
    st.session_state.email = ""

def login():
    st.title("Connexion")
    email_input = st.text_input("Email")
    password_input = st.text_input("Password", type="password")

    if st.button("Se connecter"):
        r = requests.post(f"{API_URL}/login", data={"username": email_input, "password": password_input})
        if r.status_code == 200:
            st.session_state.token = r.json()["access_token"]
            st.session_state.email = email_input
            st.rerun()
        else:
            st.error("Identifiants invalides")

# Si pas connecté → login uniquement
if not st.session_state.token:
    login()
    st.stop()

page = render_sidebar()

from modules.cameras import render as render_cameras

# -----------------
# Dashboard (après login)
# -----------------
if page == "🏠 Tableau de bord":

    st.markdown("""
    # 🛡️ VIDA Secure AI

    ### Surveillance intelligente 24h/24 • 7j/7
    """)

    # ⚠️ Si tu n'as pas de logo
    # st.image("assets/logo.png", width=200)

# -----------------
# Header autorisation
# -----------------
headers = {"Authorization": f"Bearer {st.session_state.token}"}
email = st.session_state.email

# -----------------
# Bouton Paystack
# -----------------
if st.button("Payer 79 € avec Paystack (Test)", use_container_width=True):
    with st.spinner("Redirection vers Paystack (test)..."):
        try:
            r = requests.post(f"{API_URL}/create-paystack-checkout", headers=headers)
            data = r.json()
            if "url" in data:
                st.markdown(f'<meta http-equiv="refresh" content="0; url={data["url"]}">', unsafe_allow_html=True)
            else:
                st.error("Erreur Paystack")
                st.write(data)
        except Exception as e:
            st.error("Erreur connexion au backend")
            st.write(str(e))

# -----------------
# Récup caméras
# -----------------
r = requests.get(f"{API_URL}/cameras", headers=headers)
cameras = r.json() if r.status_code == 200 else []

st.write("Status API :", r.status_code)
st.write("Réponse API :", r.text)

st.write(cameras)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📹 Caméras", len(cameras))

with col2:
    st.metric("🚨 Incidents", "--")

with col3:
    st.metric("🛡️ Zones", "--")

with col4:
    st.metric("🟢 Système", "En ligne")

if not cameras:  
    st.warning("Aucune caméra configurée")
    st.stop()

# -----------------
# Affichage des caméras (V1)
# -----------------

num_cols = 1 if len(cameras) <= 1 else 2 if len(cameras) <= 4 else 3
cols = st.columns(num_cols)

for i, cam in enumerate(cameras):

    with cols[i % num_cols]:
        
        render_camera_card(cam)


# -----------------
# Vérif paiement
# -----------------
r_user = requests.get(f"{API_URL}/me", headers=headers)
user_data = r_user.json()
        
if not user_data.get("paid"):
    st.warning("Abonnement inactif")
    if st.button("Réactiver abonnement"):
        r = requests.post(f"{API_URL}/create-checkout", headers=headers)
        st.markdown(f"[Payer maintenant]({r.json()['url']})")
    st.stop()
