import cv2

def preprocess(image):
    image = cv2.resize(image, (600, 400))
    return image