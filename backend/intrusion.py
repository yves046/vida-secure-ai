import cv2
import time

def start_detection(rtsp_url, create_alert_callback):
    cap = cv2.VideoCapture(rtsp_url)

    prev_frame = None
    last_detection_time = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Erreur caméra")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if prev_frame is None:
            prev_frame = gray
            continue

        diff = cv2.absdiff(prev_frame, gray)
        _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)

        motion_score = thresh.sum()

        if motion_score > 8000000 and time.time() - last_detection_time > 10:
            last_detection_time = time.time()
            print("INTRUSION DETECTEE")

            filename = record_video(cap)

            create_alert_callback(filename)

            time.sleep(5)  # éviter spam

        prev_frame = gray


def record_video(cap):
    import time

    ret, frame = cap.read()
    if not ret:
        return None

    filename = f"intrusion_{int(time.time())}.mp4"
    filepath = f"videos/{filename}"

    out = cv2.VideoWriter(
        filepath,
        cv2.VideoWriter_fourcc(*'avc1'),
        20.0,
        (frame.shape[1], frame.shape[0])
    )

    for _ in range(100):
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)

    out.release()

    return filename
