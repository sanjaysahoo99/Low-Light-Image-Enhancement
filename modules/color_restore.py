import cv2
import numpy as np

def restore_color(image):

    # Convert BGR to HSV
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    h, s, v = cv2.split(hsv)

    # Reduce excessive saturation
    s = s.astype(np.float32)

    # Mild saturation enhancement
    s = s * 1.05

    # Keep values in valid range
    s = np.clip(s, 0, 255).astype(np.uint8)

    # Merge channels
    restored = cv2.merge((h, s, v))

    # Convert back to BGR
    return cv2.cvtColor(restored, cv2.COLOR_HSV2BGR)