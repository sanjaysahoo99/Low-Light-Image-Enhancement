import cv2
from skimage.metrics import peak_signal_noise_ratio
from skimage.metrics import structural_similarity

def evaluate(original, enhanced):

    psnr = peak_signal_noise_ratio(original, enhanced)

    gray1 = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(enhanced, cv2.COLOR_BGR2GRAY)

    ssim = structural_similarity(gray1, gray2)

    return psnr, ssim