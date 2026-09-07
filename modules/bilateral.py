import cv2

def bilateral_filter(image):
    return cv2.bilateralFilter(
        image,
        9,
        75,
        75
    )