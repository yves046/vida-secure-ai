import json
from datetime import datetime, timedelta

client_name = input("Nom du client : ")
cameras = int(input("Nombre de caméras : "))
duration_days = int(input("Durée licence (jours) : "))

expiration = (
    datetime.now() +
    timedelta(days=duration_days)
).strftime("%Y-%m-%d")

rtsp_streams = []

for i in range(cameras):
    rtsp = input(
        f"Flux RTSP caméra {i+1} : "
    )

    rtsp_streams.append(rtsp)

license_data = {
    "client": client_name,
    "expiration": expiration,
    "cameras": cameras,
    "rtsp_streams": rtsp_streams
}

filename = (
    f"license_{client_name.replace(' ', '_')}.json"
)

with open(filename, "w") as f:
    json.dump(
        license_data,
        f,
        indent=4
    )

print("Licence créée :", filename)
