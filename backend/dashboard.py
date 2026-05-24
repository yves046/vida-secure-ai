import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(page_title='VIDA Premium Dashboard', layout='wide')

st.title('VIDA SECURE AI')
st.caption('Protection intelligente 24h/24 • Dashboard Premium')

# Sidebar
st.sidebar.header('Sites clients')
site = st.sidebar.selectbox('Choisir un site', ['Magasin Test', 'Pharmacie Cocody', 'Villa Riviera'])
status = st.sidebar.toggle('Surveillance active', value=True)

# Top metrics
c1,c2,c3,c4 = st.columns(4)
with c1:
    st.metric('Site', site)
with c2:
    st.metric('Statut', 'Actif' if status else 'Arrêté')
with c3:
    st.metric('Alertes (30j)', '12')
with c4:
    renew = (datetime.now()+timedelta(days=18)).strftime('%d/%m/%Y')
    st.metric('Renouvellement', renew)

# Main sections
left,right = st.columns([2,1])
with left:
    st.subheader('Configuration surveillance')
    h1,h2 = st.columns(2)
    with h1:
        start = st.slider('Début',0,23,22)
    with h2:
        end = st.slider('Fin',0,23,6)
    zones = st.multiselect('Zones surveillées', ['Entrée','Parking','Stock','Caisse','Portail'], default=['Entrée'])
    if st.button('Enregistrer paramètres'):
        st.success('Paramètres enregistrés')

    st.subheader('Historique alertes')
    st.dataframe([
        {'Date':'18/04/2026 02:14','Type':'Intrusion','Zone':'Entrée'},
        {'Date':'17/04/2026 23:08','Type':'Mouvement','Zone':'Parking'},
        {'Date':'16/04/2026 01:41','Type':'Intrusion','Zone':'Stock'},
    ], use_container_width=True)

with right:
    st.subheader('Abonnement')
    st.info('Plan Premium Mensuel')
    st.metric('Montant', '50 000 FCFA')
    st.button('Payer maintenant')

    st.subheader('Contact support')
    st.write('WhatsApp assistance')
    st.write('Email support')

    st.subheader('Système')
    st.success('Caméra connectée')
    st.success('Email opérationnel')
    st.success('PDF actif')

