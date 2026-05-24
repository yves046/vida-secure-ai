import streamlit as st
import json
import os
from datetime import datetime, timedelta

PAY_URL = "https://ton-lien-paiement.com"

st.set_page_config(page_title="VIDA Business", layout="wide")


# =====================================================
# DATA
# =====================================================

def load_clients():
    if os.path.exists("clients.json"):
        with open("clients.json", "r") as f:
            return json.load(f)
    return []

def load_payments():
    if os.path.exists("payments.json"):
        with open("payments.json", "r") as f:
            return json.load(f)
    return []


def save_payments(data):
    with open("payments.json", "w") as f:
        json.dump(data, f, indent=2)

def save_clients(data):
    with open("clients.json", "w") as f:
        json.dump(data, f, indent=2)


def renew_client(site):
    clients = load_clients()
    payments = load_payments()

    for c in clients:
        if c["site"] == site:
            c["paid"] = True
            c["expires"] = str(datetime.now().date() + timedelta(days=30))

            payments.append({
                "site": site,
                "amount": c["price"],
                "date": str(datetime.now().date()),
                "method": "Wave"
            })

    save_clients(clients)
    save_payments(payments)

clients = load_clients()

if not clients:
    st.error("Aucun client trouvé")
    st.stop()

# =====================================================
# KPI GLOBAL
# =====================================================

today = datetime.now().date()

active = 0
expired = 0
revenue = 0

for c in clients:
    exp = datetime.strptime(c["expires"], "%Y-%m-%d").date()

    if c["paid"] and exp >= today:
        active += 1
        revenue += c["price"]
    else:
        expired += 1

# =====================================================
# HEADER
# =====================================================

st.title("VIDA Secure AI")
st.caption("Dashboard Business Réel")

soon = 0

for c in clients:
    exp = datetime.strptime(c["expires"], "%Y-%m-%d").date()
    days = (exp - today).days

    if 0 <= days <= 3:
        soon += 1

if soon > 0:
    st.warning(f"{soon} client(s) expire(nt) bientôt")

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Clients actifs", active)
k2.metric("Clients expirés", expired)
k3.metric("Total clients", len(clients))
k4.metric("Revenu mensuel", f"{revenue:,} FCFA")
annual = revenue * 12
k5.metric("Revenu annuel", f"{annual:,} FCFA")

st.divider()
st.subheader("Projection Croissance")

p1, p2 = st.columns(2)

p1.info(f"+5 clients = {(revenue + 250000):,} FCFA / mois")
p2.info(f"+10 clients = {(revenue + 500000):,} FCFA / mois")

# =====================================================
# SELECT CLIENT
# =====================================================

sites = [c["site"] for c in clients]

site = st.sidebar.selectbox("Choisir un site", sites)

selected = next(c for c in clients if c["site"] == site)

exp = datetime.strptime(selected["expires"], "%Y-%m-%d").date()

status = "Actif" if selected["paid"] and exp >= today else "Suspendu"

# =====================================================
# CLIENT CARD
# =====================================================

st.subheader(selected["site"])

c1, c2 = st.columns(2)

with c1:
    st.write("📧 Email :", selected["email"])
    st.write("💳 Paiement :", "Oui" if selected["paid"] else "Non")
    st.write("📅 Expire :", selected["expires"])

with c2:
    st.write("📦 Plan :", selected["plan"])
    st.write("💰 Prix :", f'{selected["price"]:,} FCFA')
    st.write("🟢 Statut :" if status=="Actif" else "🔴 Statut :", status)

# =====================================================
# PREMIUM INFOS
# =====================================================

st.divider()
st.subheader("Configuration Sécurité")

st.write("📷 Caméra : Entrée Principale")
st.write("📍 Zone : Porte principale")
st.write("🕒 Horaires : 22h00 → 06h00")

# =====================================================
# ACTIONS
# =====================================================

st.divider()
st.subheader("Actions rapides")

a1, a2, a3, a4 = st.columns(4)

a1.button("▶ Démarrer", key="start")
a2.button("■ Stop", key="stop")

if a3.button("🔄 Renouveler", key="renew"):
    renew_client(site)
    st.success("Client renouvelé +30 jours")
    st.rerun()

a4.link_button("💳 Paiement", PAY_URL)

b1, b2, b3 = st.columns(3)

with b1:
    if st.button("🔴 Suspendre", key="suspend"):
        for c in clients:
            if c["site"] == site:
                c["paid"] = False
        save_clients(clients)
        st.rerun()

with b2:
    if st.button("🟢 Réactiver", key="reactivate"):
        for c in clients:
            if c["site"] == site:
                c["paid"] = True
        save_clients(clients)
        st.rerun()

with b3:
    if st.button("🗑 Supprimer", key="delete"):
        clients = [c for c in clients if c["site"] != site]
        save_clients(clients)
        st.rerun()

# =====================================================
# WARNING
# =====================================================

if status != "Actif":
    st.error("Client suspendu - paiement requis")
else:
    st.success("Système autorisé")

# =====================================================
# TOUS LES CLIENTS
# =====================================================

st.divider()
st.subheader("Portefeuille Clients")

rows = []

for c in clients:
    exp = datetime.strptime(c["expires"], "%Y-%m-%d").date()

    if c["paid"] and exp >= today:
        statut = "Actif"
    else:
        statut = "Suspendu"

    rows.append({
        "Site": c["site"],
        "Statut": statut,
        "Expire": c["expires"],
        "Plan": c["plan"],
        "Prix": c["price"]
    })

st.dataframe(rows, use_container_width=True)

# =====================================================
# AJOUT CLIENT
# =====================================================

st.divider()
st.subheader("➕ Ajouter un client")

with st.form("add_client"):

    new_site = st.text_input("Nom du site")
    new_email = st.text_input("Email")
    new_plan = st.selectbox("Plan", ["Premium"])
    new_price = st.number_input("Prix", value=50000)
    new_days = st.number_input("Durée (jours)", value=30)

    submit = st.form_submit_button("Créer client")

    if submit:

        new_exp = str(datetime.now().date() + timedelta(days=int(new_days)))

        clients.append({
            "site": new_site,
            "email": new_email,
            "paid": True,
            "expires": new_exp,
            "plan": new_plan,
            "price": int(new_price)
        })

        save_clients(clients)

        st.success("Client ajouté")
        st.rerun()


st.divider()
st.subheader("Historique Paiements")

payments = load_payments()

if payments:
    st.dataframe(payments, use_container_width=True)
else:
    st.info("Aucun paiement enregistré")


st.divider()
st.subheader("Clients à relancer")

for c in clients:
    exp = datetime.strptime(c["expires"], "%Y-%m-%d").date()
    days = (exp - today).days

    if days <= 3:
        st.warning(f"{c['site']} expire le {c['expires']}")

        msg = f"""Bonjour,
Votre abonnement VIDA Secure AI pour {c['site']} expire bientôt.

Renouvellement : {c['price']} FCFA

Merci."""
        st.code(msg)
