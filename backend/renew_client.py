import json
import sys
from datetime import datetime, timedelta

if len(sys.argv) < 2:
    print("Usage: python renew_client.py 'Nom du site'")
    exit()

SITE = sys.argv[1]

with open("clients.json", "r") as f:
    clients = json.load(f)

found = False

for c in clients:
    if c["site"].lower() == SITE.lower():
        new_date = datetime.now().date() + timedelta(days=30)

        c["paid"] = True
        c["expires"] = str(new_date)

        found = True
        print(f"{c['site']} renouvelé jusqu'au {new_date}")

with open("clients.json", "w") as f:
    json.dump(clients, f, indent=2)

if not found:
    print("Client introuvable")
