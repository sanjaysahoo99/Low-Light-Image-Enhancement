"""
make_comparisons.py
-------------------
Generates 3-panel comparison figures for 5 representative LOL test images:

    LOW-LIGHT INPUT | OUR ENHANCED OUTPUT | GROUND TRUTH

Saves to results/LOL/comparisons/
Does NOT modify any existing module or algorithm.
"""

import os
import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import config
from modules.image_io      import load_image
from modules.preprocessing import preprocess
from modules.gamma         import gamma_correction
from modules.clahe         import apply_clahe
from modules.bilateral     import bilateral_filter
from modules.color_restore import restore_color
from modules.evaluation    import evaluate

COMPARISON_DIR = os.path.join("results", "LOL", "comparisons")
SUPPORTED_EXT  = {".png", ".jpg", ".jpeg"}

# 5 representative images selected across the full PSNR range:
#   780.png  — best  result  (PSNR 22.32)
#   748.png  — above average (PSNR 21.10)
#     1.png  — near  average (PSNR 13.57)
#   111.png  — below average (PSNR 11.33)
#    23.png  — worst result  (PSNR  8.59)
SELECTED = ["780.png", "748.png", "1.png", "111.png", "23.png"]


def find_groundtruth(filename, gt_dir):
    stem, ext = os.path.splitext(filename)
    candidate = os.path.join(gt_dir, filename)
    if os.path.isfile(candidate):
        return candidate
    for alt_ext in SUPPORTED_EXT - {ext.lower()}:
        candidate = os.path.join(gt_dir, stem + alt_ext)
        if os.path.isfile(candidate):
            return candidate
    return None


def run_pipeline(image):
    image = preprocess(image)
    image = gamma_correction(image, config.GAMMA)
    image = apply_clahe(image)
    image = bilateral_filter(image)
    image = restore_color(image)
    return image


def bgr_to_rgb(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def make_comparison(filename):
    stem     = os.path.splitext(filename)[0]
    low_path = os.path.join(config.DATASET_LOW, filename)
    gt_path  = find_groundtruth(filename, config.DATASET_HIGH)

    if gt_path is None:
        print(f"  [ERROR] Ground-truth not found for {filename} — skipped.")
        return False

    low_image = load_image(low_path)
    gt_image  = load_image(gt_path)
    enhanced  = run_pipeline(low_image)

    if enhanced.shape != gt_image.shape:
        gt_image = cv2.resize(
            gt_image,
            (enhanced.shape[1], enhanced.shape[0]),
            interpolation=cv2.INTER_AREA
        )

    psnr, ssim = evaluate(gt_image, enhanced)

    # ------------------------------------------------------------------ #
    # Figure
    # ------------------------------------------------------------------ #
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.patch.set_facecolor("#0d0d0d")

    panels = [
        (low_image, "LOW-LIGHT INPUT",       "#aaaaaa"),
        (enhanced,  "OUR ENHANCED OUTPUT",   "#4fc3f7"),
        (gt_image,  "GROUND TRUTH",          "#81c784"),
    ]

    for ax, (img, label, color) in zip(axes, panels):
        ax.imshow(bgr_to_rgb(img))
        ax.set_title(label, color=color, fontsize=13,
                     fontweight="bold", pad=12, fontfamily="monospace")
        ax.axis("off")
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_edgecolor(color)
            spine.set_linewidth(2.5)

    fig.suptitle(
        f"Image: {filename}    |    PSNR: {psnr:.2f} dB    |    SSIM: {ssim:.4f}",
        color="white", fontsize=12, y=1.01
    )

    plt.tight_layout(pad=1.5)

    out_path = os.path.join(COMPARISON_DIR, f"{stem}_comparison.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()

    return out_path, psnr, ssim


def main():
    os.makedirs(COMPARISON_DIR, exist_ok=True)

    print("\nGenerating comparison figures for 5 representative images...\n")
    print(f"{'#':<4} {'Filename':<12} {'Role':<18} {'PSNR':>9} {'SSIM':>8}  Saved")
    print("-" * 72)

    roles = {
        "780.png": "Best result",
        "748.png": "Above average",
        "1.png":   "Near average",
        "111.png": "Below average",
        "23.png":  "Worst result",
    }

    for i, filename in enumerate(SELECTED, 1):
        result = make_comparison(filename)
        if result:
            out_path, psnr, ssim = result
            print(f"{i:<4} {filename:<12} {roles[filename]:<18} "
                  f"{psnr:>9.2f} {ssim:>8.4f}  {os.path.basename(out_path)}")

    print("-" * 72)
    print(f"\nAll comparisons saved to: {os.path.abspath(COMPARISON_DIR)}")
    print("\nSelected files:")
    for i, f in enumerate(SELECTED, 1):
        print(f"  {i}. {f}  ({roles[f]})")


if __name__ == "__main__":
    main()
