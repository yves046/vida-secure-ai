import streamlit as st
import cv2
import threading
import queue
import json
import requests
from PIL import Image, ImageDraw

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
        r = requests.post(f"{API_URL}/login", data={"email": email_input, "password": password_input})
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

# -----------------
# Dashboard (après login)
# -----------------
st.title("Vida Secure AI Pro - Dashboard")

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

if not cameras:  
    st.warning("Aucune caméra configurée")
    st.stop()

# -----------------
# Thread capture frames
# -----------------
def capture_frames(rtsp_url, q):
    cap = cv2.VideoCapture(rtsp_url)
    while True:
        ret, frame = cap.read()
        if ret:
            q.put(frame)
        else:
            q.put(None)

# -----------------
# Affichage grille caméras
# -----------------
num_cols = 1 if len(cameras) <= 1 else 2 if len(cameras) <= 4 else 3
cols = st.columns(num_cols)
threads = [] 
queues = []  

for i, cam in enumerate(cameras):
    with cols[i % num_cols]:
        st.subheader(cam["name"])
        placeholder = st.empty()
        q = queue.Queue(maxsize=1)
        queues.append(q)
        t = threading.Thread(target=capture_frames, args=(cam["rtsp_url"], q), daemon=True)
        t.start()
        threads.append(t)

        zones = json.loads(cam["zones_json"]) if cam["zones_json"] else []

        while True:
            frame = q.get()
            if frame is None:  
                placeholder.error("Flux interrompu")
                break   
        
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb)
            draw = ImageDraw.Draw(pil_img)

            # Dessin zones 
            for zone in zones:   
                draw.rectangle([zone["x"], zone["y"], zone["x"]+zone["w"], zone["y"]+zone["h"]], outline="red", width=3)
        
            placeholder.image(pil_img, use_column_width=True)

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
