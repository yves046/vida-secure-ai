from flask import Flask, request
import json

app = Flask(__name__)

# ------------------------
# AJOUT CAMERA
# ------------------------
@app.route("/add-camera", methods=["POST"])
def add_camera():

    data = request.json
    email = data["email"]
    rtsp = data["rtsp"]
    name = data.get("name", "Camera")

    with open("clients.json", "r") as f:
        clients = json.load(f)

    found = False

    for client in clients:
        if client["email"] == email:

            if "cameras" not in client:
                client["cameras"] = []

            client["cameras"].append({
                "name": name,
                "rtsp": rtsp,
                "status": "active"
            })

            found = True

    if not found:
        clients.append({
            "email": email,
            "active": True,
            "cameras": [
                {
                    "name": name,
                    "rtsp": rtsp,
                    "status": "active"
                }
            ]
        })

    with open("clients.json", "w") as f:
        json.dump(clients, f, indent=4)

    return {"status": "camera ajoutée"}


# ------------------------
# LANCEMENT SERVEUR
# ------------------------
if __name__ == "__main__":
    app.run(debug=True)
