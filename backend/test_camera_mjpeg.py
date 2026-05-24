import cv2

# Remplace par ton URL MJPEG
mjpeg_url = "http://Yves040:Yves46839488@10.10.11.38:8080/video"

cap = cv2.VideoCapture(mjpeg_url)

if not cap.isOpened():
    print("Impossible de se connecter à la caméra MJPEG")
    exit()

print("Connexion MJPEG réussie ! Appuyez sur 'q' pour quitter.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Frame non reçue")
        break

    cv2.imshow("Camera Tapo MJPEG", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
