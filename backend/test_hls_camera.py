import cv2
import time

cap = cv2.VideoCapture("stream.m3u8")

if not cap.isOpened():
    print("Erreur ouverture flux")
    exit()

print("Flux OK")

while True:
    ret, frame = cap.read()

    if not ret:
        print("Frame manquante, retry...")
        time.sleep(0.05)
        continue

    cv2.imshow("Camera Stable", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
