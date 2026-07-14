from ultralytics import YOLO
import cv2
import time
import threading
from queue import Queue
import numpy as np
from zones import load_camera_zones

from collections import deque

camera_states = {}
camera_states_lock = threading.Lock()


def get_camera_state(camera_id):
    with camera_states_lock:
        if camera_id not in camera_states:
            print(f"Chargement de YOLO pour la caméra {camera_id}...")

            camera_states[camera_id] = {
                "tracked_persons": {},
                "frame_buffer": deque(maxlen=100),
                "latest_frame": None,
                "frame_lock": threading.Lock(),
                "ai_queue": Queue(maxsize=1),
                "result_queue": Queue(maxsize=1),
                "model": YOLO("yolov8n.pt"),
            }

            print(f"YOLO chargé pour la caméra {camera_id}.")

        return camera_states[camera_id]

def capture_camera(cap, camera_id):

    state = get_camera_state(camera_id)
    frame_lock = state["frame_lock"]
    ai_queue = state["ai_queue"]

    while True:

        ret, frame = cap.read()

        if not ret:
            time.sleep(0.1)
            continue

        with frame_lock:
            state["latest_frame"] = frame.copy()

        if ai_queue.full():
            try:
                ai_queue.get_nowait()
            except Exception:
                pass

        try:
            ai_queue.put_nowait(frame)
        except Exception:
            pass

def ai_worker(camera_id):

    state = get_camera_state(camera_id)
    ai_queue = state["ai_queue"]
    result_queue = state["result_queue"]

    zones = []
    last_zones_reload = 0
    ZONES_RELOAD_INTERVAL = 2

    while True:

        frame = ai_queue.get()

        if frame is None:
            continue

        now = time.time()

        if now - last_zones_reload >= ZONES_RELOAD_INTERVAL:
            zones = load_camera_zones(camera_id)
            last_zones_reload = now

        detection = detect_person(
            frame,
            zones,
            camera_id
        )

        if result_queue.full():
            try:
                result_queue.get_nowait()
            except Exception:
                pass

        try:
            result_queue.put_nowait(detection)
        except Exception:
            pass

def start_detection(rtsp_url, user_id, camera_id, create_alert_callback):
    state = get_camera_state(camera_id)

    frame_buffer = state["frame_buffer"]
    frame_lock = state["frame_lock"]
    result_queue = state["result_queue"]
    tracked_persons = state["tracked_persons"]

    cap = cv2.VideoCapture(rtsp_url)

    capture_thread = threading.Thread(
        target=capture_camera,
        args=(cap, camera_id),
        daemon=True
    )

    capture_thread.start()

    ai_thread = threading.Thread(
        target=ai_worker,
        args=(camera_id,),
        daemon=True
    )

    ai_thread.start()

    print("Largeur :", cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    print("Hauteur :", cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    prev_frame = None
    last_detection_time = 0

    last_detection = {
        "detected": False,
        "persons": 0,
        "best_confidence": 0,
        "boxes": []
    }

    COOLDOWN_INTRUSION = 30
    MIN_PRESENCE = 2   # secondes dans la zone avant alerte

    zones = []
    last_zones_reload = 0
    ZONES_RELOAD_INTERVAL = 2

    while True:

        now = time.time()

        if now - last_zones_reload >= ZONES_RELOAD_INTERVAL:
            zones = load_camera_zones(camera_id)
            last_zones_reload = now

        with frame_lock:
            if state["latest_frame"] is None:
                time.sleep(0.01)
                continue

            frame = state["latest_frame"].copy()

        frame_buffer.append(frame.copy())

        for zone in zones:

            pts = np.array(zone["points"], np.int32)
            pts = pts.reshape((-1, 1, 2))

            cv2.polylines(
                frame,
                [pts],
                True,
                (0, 0, 255),
                2
            )

            cv2.putText(
                frame,
                zone["name"],
                tuple(zone["points"][0]),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2
            )

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if prev_frame is None:
            prev_frame = gray
            continue

        diff = cv2.absdiff(prev_frame, gray)
        _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)

        motion_score = thresh.sum()

        # Récupération du dernier résultat IA
        if not result_queue.empty():
            last_detection = result_queue.get()

        detection = last_detection

        intrusion_confirmed = False
        triggered_zone_name = None
        triggered_persons_count = 0
        triggered_intrusion_duration = 0

        for person in detection["boxes"]:

            track_id = person["track_id"]

            if (
                person["inside_zone"]
                and track_id is not None
                and track_id in tracked_persons
                and tracked_persons[track_id]["zone_name"] == person["zone_name"]
                and tracked_persons[track_id]["zone_duration"] >= MIN_PRESENCE
            ):
                intrusion_confirmed = True
                triggered_zone_name = person["zone_name"]
                break

        if triggered_zone_name is not None:

            persons_in_triggered_zone = [
                person
                for person in detection["boxes"]
                if (
                    person.get("inside_zone")
                    and person.get("zone_name") == triggered_zone_name
                )
            ]

            triggered_persons_count = len(
                persons_in_triggered_zone
            )

            triggered_intrusion_duration = max(
                (
                    float(person.get("zone_duration", 0))
                    for person in persons_in_triggered_zone
                ),
                default=0
            )

        if (
            motion_score > 8000000
            and intrusion_confirmed
            and time.time() - last_detection_time > COOLDOWN_INTRUSION
        ):


            annotated_frame = draw_detections(
                frame.copy(),
                detection
            )

            if not detection["detected"]:
                prev_frame = gray
                cleanup_tracked_persons(camera_id)
                continue

            print(
                f"YOLO : {detection['persons']} personne(s) "
                f"(confiance {detection['best_confidence']:.2f})"
            )

            last_detection_time = time.time()

            print("PERSONNE DÉTECTÉE PAR YOLO")

            threading.Thread(
                target=create_alert_callback,
                args=(
                    user_id,
                    camera_id,
                    triggered_zone_name,
                    triggered_persons_count,
                    triggered_intrusion_duration,
                    detection
                ),
                daemon=True
            ).start()

            time.sleep(1)  # éviter spam

        cleanup_tracked_persons(camera_id)

        prev_frame = gray

def person_in_zone(box, zones):

    x_center = (box["x1"] + box["x2"]) // 2
    y_bottom = box["y2"]

    point = (x_center, y_bottom)

    for zone in zones:

        pts = np.array(zone["points"], np.int32)

        if cv2.pointPolygonTest(
            pts,
            point,
            False
        ) >= 0:

            return zone["name"]

    return None

def detect_person(frame, zones, camera_id):

    state = get_camera_state(camera_id)
    tracked_persons = state["tracked_persons"]
    model = state["model"]

    small_frame = cv2.resize(frame, (640, 360))

    results = model.track(
        small_frame,
        persist=True,
        verbose=False,
        classes=[0],
        conf=0.60,
        imgsz=416,
        stream=False
    )

    persons = 0
    best_confidence = 0
    boxes = []

    for result in results:

        if result.boxes is None:
            continue

        for box in result.boxes:

            class_id = int(box.cls[0])
            confidence = float(box.conf[0])

            track_id = None

            if box.id is not None:
                track_id = int(box.id[0])

            if class_id != 0:
                continue

            if confidence < 0.60:
                continue

            if confidence > best_confidence:
                best_confidence = confidence

            scale_x = frame.shape[1] / 640
            scale_y = frame.shape[0] / 360

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            x1 = int(x1 * scale_x)
            y1 = int(y1 * scale_y)
            x2 = int(x2 * scale_x)
            y2 = int(y2 * scale_y)

            box_data = {
                "track_id": track_id,
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "confidence": confidence
            }

            zone_name = person_in_zone(
                box_data,
                zones
            )

            box_data["inside_zone"] = zone_name is not None
            box_data["zone_name"] = zone_name

            if box_data["inside_zone"]:
                persons += 1

#            print(
#                f"Zone : {'OUI' if box_data['inside_zone'] else 'NON'}"
#            )    

            boxes.append(box_data)

            if track_id is not None:

                now = time.time()

                if track_id not in tracked_persons:

                    tracked_persons[track_id] = {
                        "first_seen": now,
                        "last_seen": now,
                        "frames": 1,
                        "duration": 0,
                        "zone_name": None,
                        "zone_entered_at": None,
                        "zone_duration": 0
                    }

                    print(f"Nouvelle personne : ID {track_id}")

                else:

                    tracked_persons[track_id]["last_seen"] = now
                    tracked_persons[track_id]["frames"] += 1

                duration = (
                    tracked_persons[track_id]["last_seen"]
                    - tracked_persons[track_id]["first_seen"]
                )

                tracked_persons[track_id]["duration"] = duration

                current_zone = box_data["zone_name"]
                tracked = tracked_persons[track_id]

                if current_zone is not None:

                    if (
                        tracked["zone_name"] != current_zone
                        or tracked["zone_entered_at"] is None
                    ):
                        tracked["zone_name"] = current_zone
                        tracked["zone_entered_at"] = now
                        tracked["zone_duration"] = 0

                    else:
                        tracked["zone_duration"] = (
                            now - tracked["zone_entered_at"]
                        )

                else:
                    tracked["zone_name"] = None
                    tracked["zone_entered_at"] = None
                    tracked["zone_duration"] = 0

                box_data["zone_duration"] = tracked["zone_duration"]

                print(
                    f"ID {track_id} | "
                    f"Présence totale : {duration:.1f}s | "
                    f"Zone : {current_zone or 'HORS ZONE'} | "
                    f"Durée zone : {tracked['zone_duration']:.1f}s | "
                    f"Frames : {tracked['frames']}"
                )

    for person in boxes:

        print(
            f"ID={person['track_id']} "
            f"Confiance={person['confidence']:.2f}"
        )

    return {
        "detected": persons > 0,
        "persons": persons,
        "best_confidence": best_confidence,
        "boxes": boxes
    }

def draw_detections(frame, detection):

    for box in detection["boxes"]:

        x1 = box["x1"]
        y1 = box["y1"]
        x2 = box["x2"]
        y2 = box["y2"]

        confidence = box["confidence"]

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            f"Person {confidence:.2f}",
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2
        )

    return frame

def cleanup_tracked_persons(camera_id, timeout=5):

    state = get_camera_state(camera_id)
    tracked_persons = state["tracked_persons"]

    now = time.time()

    ids_to_remove = []

    for track_id, person in tracked_persons.items():

        if now - person["last_seen"] > timeout:

            print(
                f"Personne {track_id} sortie après "
                f"{person['duration']:.1f} secondes"
            )

            ids_to_remove.append(track_id)

    for track_id in ids_to_remove:

        del tracked_persons[track_id]

def record_video(frames, detection):

    import time

    if len(frames) == 0:
        return None

    timestamp = int(time.time())

    filename = f"intrusion_{timestamp}.mp4"
    filepath = f"videos/{filename}"

    image_filename = f"intrusion_{timestamp}.jpg"

    first_frame = frames[0].copy()

    annotated_frame = draw_detections(
        first_frame,
        detection
    )

    cv2.imwrite(
        image_filename,
        annotated_frame
    )

    print("Image sauvegardée :", image_filename)

    out = cv2.VideoWriter(
        filepath,
        cv2.VideoWriter_fourcc(*'avc1'),
        20.0,
        (
            first_frame.shape[1],
            first_frame.shape[0]
        )
    )

    print("VideoWriter ouvert :", out.isOpened())

    for frame in frames:

        annotated = draw_detections(
            frame.copy(),
            detection
        )

        out.write(annotated)

    out.release()

    return {
        "video": filepath,
        "image": image_filename
    }