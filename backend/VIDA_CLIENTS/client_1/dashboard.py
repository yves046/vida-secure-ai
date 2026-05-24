import streamlit as st
import subprocess
import os
import signal
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="VIDA Secure AI", layout="wide")

PID_FILE = "vida.pid"

def is_running():
    return os.path.exists(PID_FILE)

def start_system():
    if not is_running():
        p = subprocess.Popen(["python", "motion_detection.py"])
        with open(PID_FILE, "w") as f:
            f.write(str(p.pid))

def stop_system():
    if os.path.exists(PID_FILE):
        with open(PID_FILE) as f:
            pid = int(f.read())
        try:
            os.kill(pid, signal.SIGTERM)
        except:
            pass
        os.remove(PID_FILE)

st.title("🛡️ VIDA Secure AI")
st.caption("Surveillance intelligente 24h/24")

running = is_running()

c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Client", "Magasin Test")

with c2:
    st.metric("Statut", "ACTIF" if running else "ARRÊT")

with c3:
    if os.path.exists("alerts.csv"):
        lines = sum(1 for _ in open("alerts.csv"))
    else:
        lines = 0
    st.metric("Alertes Totales", lines)

col1, col2 = st.columns(2)

with col1:
    if st.button("▶️ Démarrer", use_container_width=True):
        start_system()
        st.rerun()

with col2:
    if st.button("⛔ Arrêter", use_container_width=True):
        stop_system()
        st.rerun()

st.divider()

st.subheader("Historique des alertes")

if os.path.exists("alerts.csv") and os.path.getsize("alerts.csv") > 0:
    df = pd.read_csv(
        "alerts.csv",
        names=["Date", "Client", "Caméra", "Type"]
    )
    st.dataframe(df.tail(10), use_container_width=True)
else:
    st.success("Aucune alerte enregistrée")

st.caption(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
