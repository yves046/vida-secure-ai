import subprocess
import cv2
import numpy as np

url = "rtsp://Yves040:Yves46839488@10.10.10.33:554/stream1"

command = [
    "ffmpeg",
    "-rtsp_transport", "tcp",
    "-fflags", "nobuffer",
    "-flags", "low_delay",
    "-i", url,
    "-vf", "scale=1280:720",  # 🔥 réduit charge CPU
    "-f", "rawvideo",
    "-pix_fmt", "bgr24",
    "-an",
    "-"
]

pipe = subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=10**8)

width = 1280
height = 720

while True:
    raw_frame = pipe.stdout.read(width * height * 3)

    if len(raw_frame) != width * height * 3:
        print("❌ Frame invalide")
        break

    frame = np.frombuffer(raw_frame, np.uint8).reshape((height, width, 3))

    cv2.imshow("VIDA AI CAMERA", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

pipe.terminate()
cv2.destroyAllWindows()
