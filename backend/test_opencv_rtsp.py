import cv2

url = "rtsp://Yves040:Yves46839488@10.10.10.33:554/stream1"

cap = cv2.VideoCapture(url)

# Réduit le lag
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

if not cap.isOpened():
    print("❌ Impossible d’ouvrir le flux")
    exit()

print("✅ Flux ouvert")

while True:
    ret, frame = cap.read()

    if not ret:
        print("❌ Erreur lecture frame")
        break

    cv2.imshow("Camera TEST", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
