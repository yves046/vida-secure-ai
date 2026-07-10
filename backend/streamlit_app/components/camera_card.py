import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"


def render_camera_card(camera):

    with st.container(border=True):

        # En-tête
        col1, col2 = st.columns([4, 1])

        with col1:
            st.markdown(f"### 📷 {camera['camera_name']}")

        with col2:
            status = camera.get("status", "ACTIVE")

            if status == "ACTIVE":
                st.success("🟢 En ligne")
            else:
                st.error("🔴 Hors ligne")

        st.write(f"**🏢 Site :** {camera.get('site_name', 'Non défini')}")
        st.write(f"**📍 Emplacement :** {camera.get('location', 'Non défini')}")

        st.image(
            f"{API_URL}/video_feed",
            use_container_width=True
        )

        st.divider()

        c1, c2, c3, c4, c5 = st.columns(5)

        with c1:
            st.button(
                "👁 Live",
                key=f"live_{camera['id']}",
                use_container_width=True
            )

        with c2:
            if st.button(
                "🧪 Tester",
                key=f"test_{camera['id']}",
                use_container_width=True
            ):

                st.info("Test de la caméra en cours...")

        with c3:
            st.button(
                "🗺 Zones",
                key=f"zones_{camera['id']}",
                use_container_width=True
            )

        with c4:
            st.button(
                "⚙ Modifier",
                key=f"edit_{camera['id']}",
                use_container_width=True
            )

        with c5:
            st.button(
                "🗑 Supprimer",
                key=f"delete_{camera['id']}",
                use_container_width=True
            )
