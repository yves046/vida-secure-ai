import json
import os
from datetime import datetime


def check_license(license_path="license.json"):

    if not os.path.exists(license_path):
        raise Exception(
            "Licence introuvable."
        )

    with open(license_path, "r") as f:
        license_data = json.load(f)

    expiration = datetime.strptime(
        license_data["expiration"],
        "%Y-%m-%d"
    )

    if datetime.now() > expiration:
        raise Exception(
            "Licence expirée."
        )

    print(
        f"Licence valide pour "
        f"{license_data['client']}"
    )

    print(
        f"Nombre de caméras autorisées : "
        f"{license_data['cameras']}"
    )

    license_data.setdefault(
        "rtsp_streams",
        []
    )

    return license_data
