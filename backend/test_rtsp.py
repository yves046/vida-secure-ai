import cv2

rtsp = "rtsp://Yves040:Yves46839488@10.10.10.33:554/stream1"

cap = cv2.VideoCapture(rtsp)

if not cap.isOpened():
    print("❌ Impossible d'ouvrir la caméra")
    exit()

print("✅ Caméra connectée")

while True:
    ret, frame = cap.read()

    if not ret:
        print("❌ Frame non reçue")
        break

    cv2.imshow("Camera", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
