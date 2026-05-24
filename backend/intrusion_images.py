import cv2
import glob
import datetime
import os
import time
import numpy as np

prev_frame = None
os.makedirs("captures", exist_ok=True)

motion_accumulator = 0  # compteur pour confirmer vrai mouvement

while True:
    files = sorted(glob.glob("frames_temp/*.jpg"))
    if not files:
        time.sleep(0.1)
        continue

    frame = cv2.imread(files[-1]).copy()

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)

    if prev_frame is None:
        prev_frame = blur
        continue

    diff = cv2.absdiff(prev_frame, blur)
    _, thresh = cv2.threshold(diff, 35, 255, cv2.THRESH_BINARY)  # ⚡ seuil augmenté
    dilated = cv2.dilate(thresh, None, iterations=2)
    contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    movement_detected = False

    for contour in contours:
        if cv2.contourArea(contour) < 3000:  # ⚡ aire minimale augmentée
            continue
        x, y, w, h = cv2.boundingRect(contour)
        cv2.rectangle(frame, (x,y), (x+w, y+h), (0,255,0), 2)
        movement_detected = True

    # ⚡ Confirmer vrai mouvement sur plusieurs frames
    if movement_detected:
        motion_accumulator += 1
    else:
        motion_accumulator = max(0, motion_accumulator - 1)

    if motion_accumulator >= 2:  # mouvement confirmé sur 2 frames consécutives
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        cv2.imwrite(f"captures/intrusion_{timestamp}.jpg", frame)
        print(f"⚠️ Intrusion détectée ! Image sauvegardée : intrusion_{timestamp}.jpg")
        motion_accumulator = 0  # reset

    prev_frame = blur
    cv2.imshow("Camera", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
