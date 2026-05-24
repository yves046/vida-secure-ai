import json
import time

# importe ta fonction IA
from analyse_video import analyse_video  # adapte le nom si nécessaire


def load_clients():
    with open("clients.json", "r") as f:
        return json.load(f)


def run_monitor():
    print("🟢 Surveillance SaaS lancée...")

    while True:

        clients = load_clients()
        print("🔁 Boucle de surveillance active...")

        for client in clients:

            if not client.get("active"):
                continue

            email = client["email"]

            for cam in client.get("cameras", []):

                if cam.get("status") != "active":
                    continue

                name = cam["name"]
                rtsp = cam["rtsp"]

                print(f"🔍 {email} → {name}")

                try:
                    # 🔥 Lancer ton analyse vidéo
                    analyse_video(rtsp, email)

                except Exception as e:
                    print(f"❌ Erreur caméra {name} :", e)

        # attendre 5 secondes avant la prochaine boucle
        time.sleep(5)


if __name__ == "__main__":
    run_monitor()
