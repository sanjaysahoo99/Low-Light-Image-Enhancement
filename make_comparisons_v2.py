"""
make_comparisons_v2.py
----------------------
Reads results/LOLv2_Real/metrics.csv, selects the top 3 images by
highest PSNR, and saves a 3-panel comparison figure for each:

    LOW-LIGHT INPUT | OUR ENHANCED OUTPUT | GROUND TRUTH

Saves to results/LOLv2_Real/comparisons/
Does NOT modify any existing module or algorithm.
"""

import os
import re
import csv
import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import config

METRICS_CSV    = os.path.join("results", "LOLv2_Real", "metrics.csv")
ENHANCED_DIR   = os.path.join("results", "LOLv2_Real", "enhanced")
COMPARISON_DIR = os.path.join("results", "LOLv2_Real", "comparisons")
LOW_DIR        = config.LOLV2_REAL_LOW
HIGH_DIR       = config.LOLV2_REAL_HIGH
SUPPORTED_EXT  = {".png", ".jpg", ".jpeg"}
TOP_N          = 3


# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #

def read_metrics(csv_path):
    """Return list of (filename, psnr, ssim) sorted by PSNR descending."""
    rows = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                rows.append((
                    row["Image Name"],
                    float(row["PSNR"]),
                    float(row["SSIM"])
                ))
            except (ValueError, KeyError):
                continue   # skip Average row and any malformed rows
    return sorted(rows, key=lambda x: x[1], reverse=True)


def find_gt(low_filename, gt_dir):
    """
    LOLv2 pairing: extract numeric ID from low filename,
    find matching normal file.
    e.g. low00763.png -> 763 -> normal00763.png
    """
    nums = re.findall(r"\d+", low_filename)
    if not nums:
        return None
    target_id = str(int(nums[-1]))
    for f in os.listdir(gt_dir):
        if os.path.splitext(f)[1].lower() in SUPPORTED_EXT:
            f_nums = re.findall(r"\d+", f)
            if f_nums and str(int(f_nums[-1])) == target_id:
                return os.path.join(gt_dir, f)
    return None


def bgr_to_rgb(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def make_comparison(rank, filename, psnr, ssim):
    stem = os.path.splitext(filename)[0]

    low_path      = os.path.join(LOW_DIR, filename)
    enhanced_path = os.path.join(ENHANCED_DIR, f"{stem}.png")
    gt_path       = find_gt(filename, HIGH_DIR)

    if not os.path.isfile(low_path):
        print(f"  [ERROR] Low-light image not found: {low_path}")
        return False
    if not os.path.isfile(enhanced_path):
        print(f"  [ERROR] Enhanced image not found: {enhanced_path}")
        return False
    if gt_path is None or not os.path.isfile(gt_path):
        print(f"  [ERROR] Ground-truth not found for: {filename}")
        return False

    low_image = cv2.imread(low_path)
    enhanced  = cv2.imread(enhanced_path)
    gt_image  = cv2.imread(gt_path)

    if low_image is None or enhanced is None or gt_image is None:
        print(f"  [ERROR] Could not read images for: {filename}")
        return False

    # ------------------------------------------------------------------ #
    # Figure
    # ------------------------------------------------------------------ #
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.patch.set_facecolor("#0d0d0d")

    panels = [
        (low_image, "LOW-LIGHT INPUT",     "#aaaaaa"),
        (enhanced,  "OUR ENHANCED OUTPUT", "#4fc3f7"),
        (gt_image,  "GROUND TRUTH",        "#81c784"),
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
        f"Rank #{rank} by PSNR  |  {filename}  |  "
        f"PSNR: {psnr:.2f} dB  |  SSIM: {ssim:.4f}",
        color="white", fontsize=12, y=1.01
    )

    plt.tight_layout(pad=1.5)

    out_path = os.path.join(COMPARISON_DIR, f"{stem}_comparison.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()

    return out_path


# ------------------------------------------------------------------ #
# Main
# ------------------------------------------------------------------ #

def main():
    os.makedirs(COMPARISON_DIR, exist_ok=True)

    if not os.path.isfile(METRICS_CSV):
        print(f"[ERROR] metrics.csv not found at: {METRICS_CSV}")
        print("Run: python evaluate_lol.py --dataset lolv2  first.")
        return

    all_results = read_metrics(METRICS_CSV)

    if not all_results:
        print("[ERROR] No valid rows found in metrics.csv.")
        return

    top = all_results[:TOP_N]

    print(f"\nTop {TOP_N} images by PSNR from LOLv2 Real evaluation:\n")
    print(f"{'Rank':<6} {'Filename':<20} {'PSNR (dB)':>10} {'SSIM':>8}")
    print("-" * 48)

    for rank, (filename, psnr, ssim) in enumerate(top, 1):
        result = make_comparison(rank, filename, psnr, ssim)
        status = os.path.basename(result) if result else "FAILED"
        print(f"#{rank:<5} {filename:<20} {psnr:>10.2f} {ssim:>8.4f}  -> {status}")

    print("-" * 48)
    print(f"\nComparisons saved to: {os.path.abspath(COMPARISON_DIR)}")


if __name__ == "__main__":
    main()
