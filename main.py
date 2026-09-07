import os
import config
from modules.image_io import load_image
from modules.preprocessing import preprocess
from modules.gamma import gamma_correction
from modules.clahe import apply_clahe
from modules.bilateral import bilateral_filter
from modules.color_restore import restore_color
from modules.evaluation import evaluate
from utils.save_images import save

psnr_list, ssim_list = [], []

low_images = sorted(os.listdir(config.DATASET_LOW))

for filename in low_images:
    low_path  = os.path.join(config.DATASET_LOW,  filename)
    high_path = os.path.join(config.DATASET_HIGH, filename)

    image     = load_image(low_path)
    reference = load_image(high_path)

    preprocessed = preprocess(image)
    gamma        = gamma_correction(preprocessed, config.GAMMA)
    clahe        = apply_clahe(gamma)
    bilateral    = bilateral_filter(clahe)
    final        = restore_color(bilateral)

    name = os.path.splitext(filename)[0]
    save(final, f"{name}_enhanced.jpg")

    try:
        psnr, ssim = evaluate(reference, final)
        psnr_list.append(psnr)
        ssim_list.append(ssim)
        print(f"{filename:10s}  PSNR: {psnr:.2f}  SSIM: {ssim:.4f}")
    except Exception as e:
        print(f"{filename}: Evaluation error - {e}")

if psnr_list:
    print("\n========== AVERAGE ==========")
    print(f"PSNR : {sum(psnr_list)/len(psnr_list):.2f}")
    print(f"SSIM : {sum(ssim_list)/len(ssim_list):.4f}")
    print("==============================")
