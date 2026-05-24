import cv2
import datetime
import os

rtsp = "rtsp://Yves040:Yves46839488@10.10.10.33:554/stream1"

cap = cv2.VideoCapture(rtsp)

if not cap.isOpened():
    print("❌ Impossible d'ouvrir la caméra")
    exit()

# dossier pour sauvegarder images et vidéos
os.makedirs("captures", exist_ok=True)

ret, frame1 = cap.read()
ret, frame2 = cap.read()

while True:
    diff = cv2.absdiff(frame1, frame2)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
    dilated = cv2.dilate(thresh, None, iterations=3)
    contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        if cv2.contourArea(contour) < 1000:  # seuil pour ignorer petit mouvement
            continue
        x, y, w, h = cv2.boundingRect(contour)
        cv2.rectangle(frame1, (x,y), (x+w, y+h), (0,255,0), 2)
        # sauvegarde capture
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        cv2.imwrite(f"captures/intrusion_{timestamp}.jpg", frame1)
        print(f"⚠️ Intrusion détectée ! Image sauvegardée : intrusion_{timestamp}.jpg")

    cv2.imshow("Camera", frame1)
    frame1 = frame2
    ret, frame2 = cap.read()
    if not ret:
        break

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
