from dotenv import load_dotenv
import os
import streamlit as st
import requests
import ffmpeg
import numpy as np
import cv2
import time

# ================= CONFIG =================

st.set_page_config(
    page_title="VIDA Secure AI",
    page_icon="🛡️",
    layout="wide"
)

# 🔥 CENTRAGE PRO
st.markdown("""
<style>
.block-container {
    max-width: 1000px;
    margin: auto;
}
</style>
""", unsafe_allow_html=True)

load_dotenv()

API_URL = "http://127.0.0.1:8000"

# ================= HEADER =================

st.title("🛡️ VIDA Secure AI")
st.markdown("### 🧠 Centre de surveillance intelligent")
st.caption("Surveillance en temps réel • Alertes automatiques • Vidéo preuve")

# ================= SESSION =================

if "token" not in st.session_state:
    st.session_state.token = None

headers = None
if st.session_state.token:
    headers = {"Authorization": f"Bearer {st.session_state.token}"}

# ================= LAYOUT =================

col1, col2 = st.columns([1.2, 1])

# ================= DROITE =================

with col2:

    st.subheader("🔐 Connexion")

    email = st.text_input("E-mail")
    password = st.text_input("Mot de passe", type="password")

    if st.button("Se connecter"):
        res = requests.post(
            f"{API_URL}/login",
            data={"email": email, "password": password}
        )

        if res.status_code == 200:
            st.session_state.token = res.json()["access_token"]
            st.success("Connecté ✅")
            st.rerun()
        else:
            st.error("Erreur login")

    st.subheader("📊 Statistiques")

    if headers:
        try:
            res = requests.get(f"{API_URL}/alerts", headers=headers)

            if res.status_code == 200:
                alerts = res.json()

                st.metric("Intrusions", len(alerts))

                for a in alerts[:5]:
                    st.caption(f"🕒 {a['timestamp']}")

            else:
                st.error("Erreur stats")

        except:
            st.error("Erreur API")
    else:
        st.info("Connecte-toi")

    st.subheader("🚨 Alertes")

    if headers:
        try:
            res = requests.get(f"{API_URL}/alerts", headers=headers)

            if res.status_code == 200:
                alerts = res.json()

                if len(alerts) == 0:
                    st.info("Aucune alerte")

                for a in alerts[:3]:
                    st.error(a["message"])
                    st.video(a["video_url"])
                    st.markdown("---")

        except:
            st.error("Erreur API")

# ================= GAUCHE =================

with col1:

    st.subheader("🎥 Caméra")

    rtsp_url = st.text_input(
        "URL RTSP",
        "rtsp://Yves040:Yves46839488@10.10.10.33:554/stream1"
    )

    start_stream = st.button("Démarrer")

    frame_placeholder = st.empty()

    if start_stream:
        st.success("Caméra active")
    else:
        st.warning("Caméra arrêtée")

    # ================= CAMERA =================

    if start_stream:

        if not headers:
            st.error("Connexion requise")

        else:

            width, height = 640, 480

            process = (
                ffmpeg
                .input(rtsp_url, rtsp_transport='tcp')
                .output('pipe:', format='rawvideo', pix_fmt='bgr24')
                .run_async(pipe_stdout=True)
            )

            prev_frame = None
            buffer_frames = []
            recording = False
            frames_to_record = 0
            last_alert_time = 0

            while True:

                try:
                    in_bytes = process.stdout.read(width * height * 3)
                except:
                    break

                if not in_bytes:
                    break

                try:
                    frame = np.frombuffer(in_bytes, np.uint8).reshape([height, width, 3])
                except:
                    continue

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.GaussianBlur(gray, (21, 21), 0)

                if prev_frame is None:
                    prev_frame = gray
                    continue

                diff = cv2.absdiff(prev_frame, gray)
                thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
                motion_score = np.sum(thresh)

                buffer_frames.append(frame.copy())
                if len(buffer_frames) > 30:
                    buffer_frames.pop(0)

                if motion_score > 3000000 and not recording:

                    if time.time() - last_alert_time > 10:
                        last_alert_time = time.time()

                        filename = f"videos/alert_{int(time.time())}.mp4"

                        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                        video_writer = cv2.VideoWriter(filename, fourcc, 20.0, (width, height))

                        for bf in buffer_frames:
                            video_writer.write(bf)

                        recording = True
                        frames_to_record = 120

                        st.warning("🚨 Intrusion détectée")

                if recording:
                    video_writer.write(frame)
                    frames_to_record -= 1

                    if frames_to_record <= 0:
                        recording = False
                        video_writer.release()

                        st.success("🎥 Vidéo enregistrée")

                        requests.post(
                            f"{API_URL}/test-alert",
                            headers=headers,
                            json={
                                "message": "Intrusion détectée",
                                "video_url": filename.split("/")[-1]
                            }
                        )

                prev_frame = gray

                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_placeholder.image(frame)

                time.sleep(0.03)

    # ================= OFFRE =================

    st.markdown("## 💼 Offre")

    st.info("""
    🔐 Surveillance intelligente  
    🎥 Enregistrement automatique  
    📡 Accès à distance  
    🚨 Alertes en temps réel  

    💰 50 000 FCFA / mois
    """)

    st.markdown("""
    <a href="https://wa.me/2250700062242" target="_blank">
        <button style="background-color:green;color:white;padding:10px;border:none;border-radius:5px;">
            📞 Installer chez moi
        </button>
    </a>
    """, unsafe_allow_html=True)
