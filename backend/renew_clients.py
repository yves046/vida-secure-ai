import json
from datetime import datetime, timedelta

SITE = "Magasin Test"

with open("clients.json", "r") as f:
    clients = json.load(f)

for c in clients:
    if c["site"] == SITE:
        today = datetime.now().date()
        new_date = today + timedelta(days=30)

        c["paid"] = True
        c["expires"] = str(new_date)

with open("clients.json", "w") as f:
    json.dump(clients, f, indent=2)

print("Paiement validé + 30 jours ajoutés")
