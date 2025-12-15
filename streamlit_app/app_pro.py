# streamlit_app/app_pro.py
import streamlit as st
import requests

st.set_page_config(page_title="Vida Secure AI – Pro", layout="centered")

st.title("Vida Secure AI – Abonnement Pro")
st.markdown("### Surveillance intelligente 24/7 – 79 €/mois")

# Retour de paiement
if st.query_params.get("success") == "true":
    st.success("Paiement réussi ! Bienvenue dans Vida Secure Pro")
    st.balloons()
    st.session_state.paid = True

if st.query_params.get("cancel") == "true":
    st.warning("Paiement annulé – tu peux réessayer")

# Page de paiement
if "paid" not in st.session_state:
   import streamlit as st
import requests

st.set_page_config(page_title="Vida Secure AI – Pro", layout="centered")

st.title("Vida Secure AI – Abonnement Pro")
st.markdown("### Surveillance intelligente 24/7 – 79 €/mois")

# Retour de paiement
if st.query_params.get("success") == "true":
    st.success("Paiement réussi ! Bienvenue dans Vida Secure Pro")
    st.session_state.paid = True

if st.query_params.get("cancel") == "true":
    st.warning("Paiement annulé – tu peux réessayer")

# 👇 ICI TU COLLES LE CODE FINAL MOBILE
if "paid" not in st.session_state:
    # ⬅️ CODE FINAL QUE JE T’AI DONNÉ
    ...
else:
    st.success("Accès Premium activé !")

                    st.link_button(
                        "Continuer vers le paiement sécurisé Stripe",
                        data["url"],
                        use_container_width=True
                    )

                    st.caption("Si le bouton ne s’ouvre pas, copie ce lien et ouvre-le dans ton navigateur 👇")
                    st.code(data["url"])

                else:
                    st.error(f"Erreur Stripe : {data.get('error')}")

            except:
                st.error("Le serveur met un peu de temps à répondre, réessaie dans un instant")



# Accès Premium
else:
    st.success("Accès Premium activé !")
    rtsp = st.text_input("URL RTSP de ta caméra", 
                         value="rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mov")
    if st.button("Lancer la surveillance"):
        st.video(rtsp)
        st.write("Détection IA active (intrus, sacs abandonnés, etc.)")
