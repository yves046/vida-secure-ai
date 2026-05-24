import cv2

# Remplace par l'IP de ta caméra
rtsp_url = "rtsp://Yves040:Yves46839488@10.10.10.33:554/stream1"

# Force l'utilisation de FFMPEG
cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)

if not cap.isOpened():
    print("Impossible de se connecter à la caméra avec FFMPEG")
    exit()

print("Connexion RTSP OK ✅")

# Lire 50 frames pour tester
for i in range(50):
    ret, frame = cap.read()
    if not ret:
        print("Frame non reçue")
        break
    print(f"Frame {i} reçue, dimensions: {frame.shape}")

cap.release()
