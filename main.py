from modules.image_io import load_image
from modules.preprocessing import preprocess
from modules.gamma import gamma_correction
from modules.clahe import apply_clahe
from modules.bilateral import bilateral_filter
from modules.color_restore import restore_color
from modules.evaluation import evaluate

from utils.save_images import save

import config

# -----------------------
# Load Image
# -----------------------
image = load_image(config.INPUT_IMAGE)

# -----------------------
# Preprocessing
# -----------------------
preprocessed = preprocess(image)

# -----------------------
# Gamma Correction
# -----------------------
gamma = gamma_correction(preprocessed, config.GAMMA)

# -----------------------
# CLAHE
# -----------------------
clahe = apply_clahe(gamma)

# -----------------------
# Bilateral Filter
# -----------------------
bilateral = bilateral_filter(clahe)

# -----------------------
# Color Restoration
# -----------------------
final = restore_color(bilateral)

# -----------------------
# Print Image Dimensions
# -----------------------
print("\n===== IMAGE SHAPES =====")
print("Original      :", image.shape)
print("Preprocessed  :", preprocessed.shape)
print("Gamma         :", gamma.shape)
print("CLAHE         :", clahe.shape)
print("Bilateral     :", bilateral.shape)
print("Final         :", final.shape)
print("========================\n")

# -----------------------
# Save Outputs
# -----------------------
save(gamma, "1_gamma.jpg")
save(clahe, "2_clahe.jpg")
save(bilateral, "3_bilateral.jpg")
save(final, "4_final.jpg")

# -----------------------
# Evaluation
# -----------------------
try:
    psnr, ssim = evaluate(preprocessed, final)

    print("----------------------------")
    print("Image Enhancement Completed")
    print("----------------------------")
    print(f"PSNR : {psnr:.2f}")
    print(f"SSIM : {ssim:.4f}")

except Exception as e:
    print("\nEvaluation Error:")
    print(e)