#!/bin/bash
echo "Installation On-Premise local"

cp -r ../backend/* . 2>/dev/null || echo "Copie backend OK ou déjà fait"
mkdir -p uploads

docker compose up -d --build

echo "Terminé"
echo "Backend : http://localhost:8000/docs"
echo "Dashboard : streamlit run ../streamlit_app/client_dashboard.py"