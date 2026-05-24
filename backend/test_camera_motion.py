import cv2

# Remplace par ton URL RTSP
rtsp_url = "rtsp://Yves040:Yves46839488@10.10.10.33:554/stream1"

cap = cv2.VideoCapture(rtsp_url)
if not cap.isOpened():
    print("Impossible de se connecter à la caméra")
    exit()

print("Connexion RTSP OK ✅")

# Lire quelques frames pour tester
for i in range(50):
    ret, frame = cap.read()
    if not ret:
        print("Frame non reçue")
        break
    # Affiche juste la taille de la frame
    print(f"Frame {i} reçue, dimensions: {frame.shape}")

cap.release()
print("Fin du test")
