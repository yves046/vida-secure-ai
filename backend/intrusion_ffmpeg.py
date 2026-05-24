import cv2
import subprocess
import numpy as np
import datetime
import os
import threading
from queue import Queue

rtsp = "rtsp://Yves040:Yves46839488@10.10.10.33:554/stream1"

# dossier pour sauvegarder images
os.makedirs("captures", exist_ok=True)

frame_width, frame_height = 640, 480

# Queue pour partager les frames entre threads
frame_queue = Queue(maxsize=10)

def ffmpeg_reader():
    """Thread qui lit les frames FFmpeg et les place dans la queue"""
    command = [
        "ffmpeg",
        "-i", rtsp,
        "-f", "image2pipe",
        "-pix_fmt", "bgr24",
        "-vcodec", "rawvideo",
        "-"
    ]
    pipe = subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=10**8)
    try:
        while True:
            raw_frame = pipe.stdout.read(frame_width * frame_height * 3)
            if len(raw_frame) != frame_width * frame_height * 3:
                continue
            frame = np.frombuffer(raw_frame, dtype=np.uint8).reshape((frame_height, frame_width, 3))
            frame_queue.put(frame.copy())
    except:
        pass
    finally:
        pipe.terminate()

# Démarrer le thread
threading.Thread(target=ffmpeg_reader, daemon=True).start()

prev_frame = None

try:
    while True:
        if frame_queue.empty():
            continue
        frame = frame_queue.get()

        # --- Détection mouvement ---
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5,5), 0)

        if prev_frame is None:
            prev_frame = blur
            continue

        diff = cv2.absdiff(prev_frame, blur)
        _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
        dilated = cv2.dilate(thresh, None, iterations=2)
        contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            if cv2.contourArea(contour) < 1000:
                continue
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x,y), (x+w, y+h), (0,255,0), 2)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            cv2.imwrite(f"captures/intrusion_{timestamp}.jpg", frame)
            print(f"⚠️ Intrusion détectée ! Image sauvegardée : intrusion_{timestamp}.jpg")

        prev_frame = blur
        cv2.imshow("Camera", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("⏹ Arrêt manuel")

finally:
    cv2.destroyAllWindows()
