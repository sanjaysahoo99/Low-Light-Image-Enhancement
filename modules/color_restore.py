import cv2

def restore_color(image):

    hsv = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2HSV
    )

    h,s,v = cv2.split(hsv)

    s = cv2.equalizeHist(s)

    hsv = cv2.merge((h,s,v))

    return cv2.cvtColor(
        hsv,
        cv2.COLOR_HSV2BGR
    )