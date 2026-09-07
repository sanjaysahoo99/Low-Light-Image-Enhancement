import cv2

def apply_clahe(image):

    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)

    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8,8)
    )

    l = clahe.apply(l)

    merged = cv2.merge((l,a,b))

    return cv2.cvtColor(
        merged,
        cv2.COLOR_LAB2BGR
    )