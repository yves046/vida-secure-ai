import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.title("Historique des alertes")

API_URL = "http://127.0.0.1:8000"
token = st.session_state.get("token")
if not token:
    st.error("Connectez-vous d'abord")
    st.stop()

headers = {"Authorization": f"Bearer {token}"}

page = st.number_input("Page", min_value=1, value=1)
r = requests.get(f"{API_URL}/alerts?page={page}", headers=headers)
data = r.json()

if not data["alerts"]:
    st.info("Aucune alerte")
else:
    df = pd.DataFrame(data["alerts"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    st.dataframe(df[["timestamp", "type", "photo_path", "clip_path", "pdf_path"]])

    st.write(f"Page {data['page']} / {data['pages']} (total: {data['total']})")

    col1, col2, col3 = st.columns(3)
    for alert in data["alerts"]:
        with st.expander(f"{alert['type']} - {alert['timestamp']}"):
            if alert["photo_path"]:
                st.image(f"{API_URL}/files/photo/{alert['photo_path'].split('/')[-1]}", caption="Photo")
            if alert["clip_path"]:
                st.video(f"{API_URL}/files/clip/{alert['clip_path'].split('/')[-1]}", format="video/mp4")
            if alert["pdf_path"]:
                st.download_button("Télécharger PDF", data=requests.get(f"{API_URL}/files/pdf/{alert['pdf_path'].split('/')[-1]}", headers=headers).content, file_name=alert['pdf_path'].split('/')[-1])