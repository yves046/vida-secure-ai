import cv2
import os

print("========== VIDA H264 DIAGNOSTIC ==========")
print("OpenCV version :", cv2.__version__)

build = cv2.getBuildInformation()
print("FFmpeg activé :", "YES" in build.split("FFMPEG:")[1].splitlines()[0])

test_path = "/tmp/vida_h264_test.mp4"

writer = cv2.VideoWriter(
    test_path,
    cv2.VideoWriter_fourcc(*"avc1"),
    20.0,
    (640, 480)
)

print("Encodeur H264 disponible :", writer.isOpened())

if writer.isOpened():
    frame = __import__("numpy").zeros((480, 640, 3), dtype="uint8")
    for _ in range(40):
        writer.write(frame)

writer.release()

print("Fichier créé :", os.path.exists(test_path))

if os.path.exists(test_path):
    print("Taille :", os.path.getsize(test_path), "octets")

print("========== FIN DIAGNOSTIC ==========")
