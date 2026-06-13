import sys
import os

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

sys.path.append(PROJECT_ROOT)

from licensing.license_checker import check_license

license_data = check_license("../license.json")

MAX_CAMERAS = license_data["cameras"]

CAMERAS_IN_USE = 1

if CAMERAS_IN_USE > MAX_CAMERAS:
    raise Exception(
        f"Licence insuffisante : "
        f"{MAX_CAMERAS} caméra(s) autorisée(s), "
        f"mais {CAMERAS_IN_USE} utilisée(s)."
    )

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image
)

from reportlab.lib.styles import getSampleStyleSheet
from mailer import send_alert
from datetime import datetime
from ultralytics import YOLO
import time
import subprocess
import cv2
import numpy as np

model = YOLO("yolov8n.pt")

WIDTH = 640
HEIGHT = 360

DEVELOPMENT_MODE = True

if (
    DEVELOPMENT_MODE
    or not license_data["rtsp_streams"]
):
    RTSP_URL = (
        "rtsp://Yves040:Yves46839488"
        "@10.10.10.33:554/stream1"
    )
else:
    RTSP_URL = (
        license_data["rtsp_streams"][0]
    )

command = [
    "ffmpeg",
    "-rtsp_transport", "tcp",
    "-i", RTSP_URL,

    "-vf",
    "scale=640:360",

    "-f",
    "image2pipe",

    "-pix_fmt",
    "bgr24",

    "-vcodec",
    "rawvideo",

    "-"
]

pipe = subprocess.Popen(
    command,
    stdout=subprocess.PIPE,
    bufsize=10**8
)

last_alert_time = 0
ALERT_DELAY = 30  # secondes

video_writer = None
recording = False
last_detection_time = 0
intrusion_start_time = 0
max_persons_detected = 0
last_image_path = None
last_video_path = None
record_end_time = 0

def create_pdf_report(image_path):

    timestamp = int(time.time())

    pdf_name = f"rapport_{timestamp}.pdf"

    doc = SimpleDocTemplate(pdf_name)

    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph(
            "RAPPORT D'INTRUSION VIDA SECURE AI",
            styles["Title"]
        )
    )

    elements.append(Spacer(1, 20))

    elements.append(
        Paragraph(
            f"Date : {time.ctime()}",
            styles["Normal"]
        )
    )

    elements.append(Spacer(1, 20))

    elements.append(Image(
        image_path,
        width=300,
        height=180
    ))

    doc.build(elements)

    print(f"PDF créé : {pdf_name}")

def process_camera(pipe):

    global recording
    global video_writer
    global last_detection_time
    global intrusion_start_time
    global max_persons_detected
    global last_image_path
    global last_video_path
    global record_end_time
    global last_alert_time

    while True:
        raw_image = pipe.stdout.read(WIDTH * HEIGHT * 3)

        if len(raw_image) != WIDTH * HEIGHT * 3:
            print("Frame perdue")
            break

        frame = np.frombuffer(
            raw_image,
            dtype=np.uint8
        ).reshape((HEIGHT, WIDTH, 3))

        frame = frame.copy()

        # Gestion de l'enregistrement
        if recording:
            video_writer.write(frame)

            print(
                "DEBUG:",
                time.time() - last_detection_time
            )

            # Arrêt 10 sec après la dernière détection
            if time.time() - last_detection_time > 10:
                recording = False

                if video_writer is not None:
                    video_writer.release()
                    video_writer = None

                intrusion_duration = int(
                    time.time() - intrusion_start_time
                )

                report_name = f"rapport_{int(time.time())}.pdf"

                pdf = SimpleDocTemplate(report_name)

                styles = getSampleStyleSheet()

                elements = []

                elements.append(
                    Paragraph(
                        "RAPPORT D'INTRUSION VIDA SECURE AI",
                        styles["Title"]
                    )
                )

                elements.append(Spacer(1, 20))

                elements.append(
                    Paragraph(
                        f"Duree intrusion : {intrusion_duration} secondes",
                        styles["Normal"]
                    )
                )

                elements.append(
                    Paragraph(
                        f"Nombre max de personnes : {max_persons_detected}",
                        styles["Normal"]
                    )
                )

                elements.append(
                    Paragraph(
                        f"Video : {last_video_path}",
                        styles["Normal"]
                    )
                )

                elements.append(Spacer(1, 20))

                if last_image_path:
                    img = Image(last_image_path)

                    img.drawWidth = 300
                    img.drawHeight = 170

                    elements.append(img)

                print("AVANT PDF")
                pdf.build(elements)
                print("APRES PDF")

                print("PDF cree :", report_name)

                send_alert(
                    to_email="yvestoure717@gmail.com",
                    timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                    intrusion_duration=intrusion_duration,
                    persons_count=max_persons_detected,
                    pdf_path=report_name,
                    image_path=last_image_path,
                    video_path=last_video_path
                )

                print("FIN VIDEO")


        results = model(frame)

        persons_in_frame = 0

        for r in results:
            for box in r.boxes:

                cls = int(box.cls[0])
                confidence = float(box.conf[0])

                if cls == 0 and confidence > 0.80:
                    print(
                        "Personne",
                        round(confidence, 2)
                    )

                    last_detection_time = time.time()

                    persons_in_frame += 1

                    # Début d'une nouvelle intrusion
                    if not recording:

                        intrusion_start_time = time.time()

                        max_persons_detected = 0

                        timestamp = int(time.time())

                        video_path = f"intrusion_{timestamp}.mp4"

                        last_video_path = video_path

                        fourcc = cv2.VideoWriter_fourcc(*"mp4v")

                        video_writer = cv2.VideoWriter(
                            video_path,
                            fourcc,
                            10,
                            (WIDTH, HEIGHT)
                        )

                        recording = True

                        print("ALERTE INTRUSION")
                        print(f"DEBUT VIDEO : {video_path}")

                        image_path = f"intrusion_{timestamp}.jpg"

                        last_image_path = image_path

                        cv2.imwrite(image_path, frame)

                        print(f"Photo sauvegardée : {image_path}")

                    current_time = time.time()

                    if current_time - last_alert_time > ALERT_DELAY:
                        last_alert_time = current_time

                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    width = x2 - x1
                    height = y2 - y1

                    if cls == 0 and confidence > 0.80 and width > 50 and height > 100:
                
                        cv2.rectangle(
                            frame,
                            (x1, y1),
                            (x2, y2),
                            (0, 255, 0),
                            2
                        )

                        cv2.putText(
                            frame,
                            "PERSONNE",
                            (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            (0, 255, 0),
                            2
                        )

        # ← ICI SEULEMENT

        max_persons_detected = max(
            max_persons_detected,
            persons_in_frame
        )

        cv2.imshow("VIDA CAMERA", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("s"):
            cv2.imwrite("person_test.jpg", frame)
            print("Image sauvée")

        if key == ord("q"):
            break

        if key == ord("q"):
            break

process_camera(pipe)

if video_writer is not None:
    video_writer.release()

pipe.terminate()
cv2.destroyAllWindows()
