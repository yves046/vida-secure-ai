import cv2
import streamlit as st

# Remplace par ton flux RTSP
rtsp_url = "rtsp://Yves040:Yves46839488@10.10.10.122:554/stream1"

# Capture vidéo
cap = cv2.VideoCapture(rtsp_url)

# Zone Streamlit pour afficher le flux
stframe = st.empty()

# Boucle pour lire le flux
while True:
    ret, frame = cap.read()
    if not ret:
        st.write("Impossible de récupérer le flux")
        break

    # Convertir BGR (OpenCV) en RGB (Streamlit)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Afficher l'image
    stframe.image(frame, channels="RGB")
