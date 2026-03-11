import cv2

rtsp = "rtsp://Yves040:Yves46839488@10.10.10.122:554/stream1"

cap = cv2.VideoCapture(rtsp)

while True:
    ret, frame = cap.read()

    if not ret:
        print("Impossible de lire le flux caméra")
        break

    cv2.imshow("Camera", frame)

    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()
