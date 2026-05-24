import cv2

# Remplace par ton URL RTSP Tapo
rtsp = "rtsp://Yves040:Yves46839488@10.10.10.33:554/stream1"

# Forcer FFMPEG et H264
cap = cv2.VideoCapture(rtsp, cv2.CAP_FFMPEG)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'H264'))

if not cap.isOpened():
    print("Impossible de se connecter à la caméra")
    exit()

print("Connexion réussie ! Appuyez sur 'q' pour quitter.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Frame non reçue")
        break

    cv2.imshow("Camera Tapo", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
