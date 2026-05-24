import cv2

rtsp_url = "rtsp://Yves040:Yves46839488@10.10.10.33:554/stream1"

cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)

if not cap.isOpened():
    print("Connexion échouée")
    exit()

print("Connexion réussie")

while True:
    ret, frame = cap.read()

    if not ret:
        print("Frame non reçue")
        break

    cv2.imshow("Camera", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
