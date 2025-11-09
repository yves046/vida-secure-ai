import cv2
import face_recognition
import numpy as np
import os
import datetime
import subprocess

# Charge le visage connu
yves_image = face_recognition.load_image_file("known_faces/yves.jpg")
yves_encoding = face_recognition.face_encodings(yves_image)[0]

known_face_encodings = [yves_encoding]
known_face_names = ["Yves"]

# Log file
log_file = "security_log.txt"

def log_event(name):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] {name} détecté\n")

def play_alert():
    subprocess.run(["afplay", "/System/Library/Sounds/Glass.aiff"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print("VIDA SECURE AI V4 - STABLE & PROPRE")
print("Appuie sur 'q' pour quitter.\n")

cap = cv2.VideoCapture(1)
if not cap.isOpened():
    cap = cv2.VideoCapture(0)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# Fenêtre unique
window_name = 'VIDA SECURE AI'
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
cv2.resizeWindow(window_name, 1280, 720)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Redimensionne pour fluidité
    small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    # Reconnaissance sur petite image
    face_locations = face_recognition.face_locations(rgb_small_frame, model="hog")
    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

    # Remet à l'échelle
    display_frame = cv2.resize(frame, (1280, 720))

    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        top *= 2
        right *= 2
        bottom *= 2
        left *= 2

        matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.5)
        name = "INCONNU"
        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
        best_match_index = np.argmin(face_distances)
        if matches[best_match_index]:
            name = known_face_names[best_match_index]

        color = (0, 255, 0) if name == "Yves" else (0, 0, 255)
        cv2.rectangle(display_frame, (left, top), (right, bottom), color, 4)
        cv2.putText(display_frame, name, (left, top-15), cv2.FONT_HERSHEY_DUPLEX, 1.2, color, 3)

        if name == "INCONNU":
            log_event(name)
            play_alert()

    # Affiche uniquement la fenêtre principale
    cv2.imshow(window_name, display_frame)

    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("Arrêt propre. Logs dans security_log.txt")
