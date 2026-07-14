import os
import json

ZONE_FOLDER = "zones"

def load_camera_zones(camera_id):
    path = os.path.join(ZONE_FOLDER, f"camera_{camera_id}.json")

    if not os.path.exists(path):
        return []

    with open(path, "r") as f:
        data = json.load(f)

    return data.get("zones", [])
