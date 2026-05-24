# VIDA SECURE AI – Dossier maître unique (Semaine 6 → MVP payant)

## Lancer le backend
uvicorn backend.main:app --reload

## Structure
- backend/      → FastAPI + Stripe
- frontend/     → à venir (React/Vite ou HTMX)
- docker/       → Dockerfiles
- logs/         → une sous-dossier par caméra
- uploads/      → vidéos temporaires
- models/       → best.pt et futurs modèles
