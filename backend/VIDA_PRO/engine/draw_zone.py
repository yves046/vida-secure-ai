import cv2
import json
import numpy as np

IMAGE_PATH = "intrusion_1776369444.jpg"

points = []

img = cv2.imread(IMAGE_PATH)
img = cv2.resize(img, (1280,720))

def mouse(event,x,y,flags,param):
    global points
    if event == cv2.EVENT_LBUTTONDOWN:
        points.append((x,y))

cv2.namedWindow("ZONE CONFIG", cv2.WINDOW_NORMAL)
cv2.resizeWindow("ZONE CONFIG",1280,720)
cv2.setMouseCallback("ZONE CONFIG", mouse)

while True:
    display = img.copy()

    for p in points:
        cv2.circle(display,p,5,(0,255,0),-1)

    if len(points)>=2:
        cv2.polylines(display,[np.array(points)],False,(0,255,0),2)

    if len(points)>=3:
        cv2.polylines(display,[np.array(points)],True,(0,0,255),2)

    cv2.imshow("ZONE CONFIG", display)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("r"):
        points=[]

    elif key == ord("s"):
        with open("zone.json","w") as f:
            json.dump(points,f)
        print("Zone sauvée")

    elif key == ord("q"):
        break

cv2.destroyAllWindows()
