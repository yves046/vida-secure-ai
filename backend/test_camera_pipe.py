import subprocess
import numpy as np
import cv2

RTSP_URL = "rtsp://Yves040:Yves46839488@10.10.10.33:554/stream1"

# Commande FFmpeg
command = [
    "ffmpeg",
    "-rtsp_transport", "tcp",
    "-i", RTSP_URL,
    "-f", "image2pipe",
    "-pix_fmt", "bgr24",
    "-vcodec", "rawvideo",
    "-"
]

pipe = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

width = 1920
height = 1080

print("Lecture du flux via FFmpeg...")

while True:
    raw_image = pipe.stdout.read(width * height * 3)
    
    if len(raw_image) != width * height * 3:
        print("Frame manquante")
        break

    frame = np.frombuffer(raw_image, np.uint8).reshape((height, width, 3))

    cv2.imshow("Flux RTSP (FFmpeg)", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cv2.destroyAllWindows()
pipe.terminate()
