"""
evaluate_lol.py
---------------
Benchmarks the existing Low-Light Image Enhancement pipeline on the
complete LOL test dataset (eval15).

Outputs
-------
  results/LOL/enhanced/          - every enhanced image
  results/LOL/metrics.csv        - per-image PSNR and SSIM
  results/LOL/summary.txt        - final averaged metrics

Does NOT modify any existing module or algorithm.
"""

import os
import csv
import cv2

import config
from modules.image_io      import load_image
from modules.preprocessing import preprocess
from modules.gamma         import gamma_correction
from modules.clahe         import apply_clahe
from modules.bilateral     import bilateral_filter
from modules.color_restore import restore_color
from modules.evaluation    import evaluate

# ------------------------------------------------------------------ #
# Paths
# ------------------------------------------------------------------ #
LOW_DIR      = config.DATASET_LOW
HIGH_DIR     = config.DATASET_HIGH
ENHANCED_DIR = os.path.join("results", "LOL", "enhanced")
CSV_PATH     = os.path.join("results", "LOL", "metrics.csv")
SUMMARY_PATH = os.path.join("results", "LOL", "summary.txt")

SUPPORTED_EXT = {".png", ".jpg", ".jpeg"}


# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #

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
    """Exact pipeline order from main.py — nothing changed."""
    image = preprocess(image)
    image = gamma_correction(image, config.GAMMA)
    image = apply_clahe(image)
    image = bilateral_filter(image)
    image = restore_color(image)
    return image


# ------------------------------------------------------------------ #
# Main
# ------------------------------------------------------------------ #

def main():
    os.makedirs(ENHANCED_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)

    low_files = sorted([
        f for f in os.listdir(LOW_DIR)
        if os.path.splitext(f)[1].lower() in SUPPORTED_EXT
    ])

    if not low_files:
        print(f"[ERROR] No images found in: {LOW_DIR}")
        return

    total      = len(low_files)
    rows       = []          # for CSV
    psnr_list  = []
    ssim_list  = []
    failed     = []

    print(f"\nLOL Evaluation — {total} images found")
    print(f"{'Image':<15} {'PSNR (dB)':>10} {'SSIM':>8}  Status")
    print("=" * 52)

    for filename in low_files:
        low_path = os.path.join(LOW_DIR, filename)
        stem     = os.path.splitext(filename)[0]

        # --- locate ground-truth ---
        gt_path = find_groundtruth(filename, HIGH_DIR)
        if gt_path is None:
            reason = "ground-truth image not found"
            print(f"{filename:<15} {'—':>10} {'—':>8}  [FAILED] {reason}")
            failed.append((filename, reason))
            rows.append([filename, "", "", "FAILED", reason])
            continue

        # --- load ---
        try:
            low_image = load_image(low_path)
            gt_image  = load_image(gt_path)
        except Exception as e:
            reason = str(e)
            print(f"{filename:<15} {'—':>10} {'—':>8}  [FAILED] {reason}")
            failed.append((filename, reason))
            rows.append([filename, "", "", "FAILED", reason])
            continue

        # --- pipeline ---
        try:
            enhanced = run_pipeline(low_image)
        except Exception as e:
            reason = f"pipeline error: {e}"
            print(f"{filename:<15} {'—':>10} {'—':>8}  [FAILED] {reason}")
            failed.append((filename, reason))
            rows.append([filename, "", "", "FAILED", reason])
            continue

        # --- dimension guard ---
        if enhanced.shape != gt_image.shape:
            gt_image = cv2.resize(
                gt_image,
                (enhanced.shape[1], enhanced.shape[0]),
                interpolation=cv2.INTER_AREA
            )

        # --- save enhanced ---
        enhanced_path = os.path.join(ENHANCED_DIR, f"{stem}.png")
        cv2.imwrite(enhanced_path, enhanced)

        # --- metrics ---
        try:
            psnr, ssim = evaluate(gt_image, enhanced)
        except Exception as e:
            reason = f"metric error: {e}"
            print(f"{filename:<15} {'—':>10} {'—':>8}  [FAILED] {reason}")
            failed.append((filename, reason))
            rows.append([filename, "", "", "FAILED", reason])
            continue

        psnr_list.append(psnr)
        ssim_list.append(ssim)
        rows.append([filename, f"{psnr:.4f}", f"{ssim:.4f}", "OK", ""])
        print(f"{filename:<15} {psnr:>10.2f} {ssim:>8.4f}  OK")

    # ------------------------------------------------------------------ #
    # Statistics
    # ------------------------------------------------------------------ #
    n = len(psnr_list)

    print("=" * 52)

    if n == 0:
        print("[ERROR] No images were successfully evaluated.")
        return

    avg_psnr = sum(psnr_list) / n
    avg_ssim = sum(ssim_list) / n
    min_psnr = min(psnr_list)
    max_psnr = max(psnr_list)
    min_ssim = min(ssim_list)
    max_ssim = max(ssim_list)

    sep = "-" * 44
    summary_lines = [
        "",
        sep,
        "       FINAL EVALUATION SUMMARY",
        sep,
        f"  Dataset          : LOL eval15",
        f"  Total images     : {total}",
        f"  Processed OK     : {n}",
        f"  Failed           : {len(failed)}",
        sep,
        f"  Avg  PSNR (dB)   : {avg_psnr:.4f}",
        f"  Min  PSNR (dB)   : {min_psnr:.4f}",
        f"  Max  PSNR (dB)   : {max_psnr:.4f}",
        sep,
        f"  Avg  SSIM        : {avg_ssim:.4f}",
        f"  Min  SSIM        : {min_ssim:.4f}",
        f"  Max  SSIM        : {max_ssim:.4f}",
        sep,
    ]

    for line in summary_lines:
        print(line)

    if failed:
        print("\nFailed images:")
        for fname, reason in failed:
            print(f"  {fname}: {reason}")

    # ------------------------------------------------------------------ #
    # Save CSV
    # ------------------------------------------------------------------ #
    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Image Name", "PSNR", "SSIM"])
        for row in rows:
            if row[3] == "OK":
                writer.writerow([row[0], row[1], row[2]])
        writer.writerow([])
        writer.writerow(["Average", f"{avg_psnr:.4f}", f"{avg_ssim:.4f}"])

    # ------------------------------------------------------------------ #
    # Save summary text
    # ------------------------------------------------------------------ #
    with open(SUMMARY_PATH, "w") as f:
        f.write("========================================\n")
        f.write("LOL DATASET EVALUATION\n")
        f.write("========================================\n\n")
        f.write(f"Dataset: LOL\n")
        f.write(f"Test Images: {total}\n\n")
        f.write(f"Average PSNR : {avg_psnr:.2f} dB\n")
        f.write(f"Average SSIM : {avg_ssim:.4f}\n\n")
        f.write(f"Minimum PSNR : {min_psnr:.2f} dB\n")
        f.write(f"Maximum PSNR : {max_psnr:.2f} dB\n\n")
        f.write(f"Minimum SSIM : {min_ssim:.4f}\n")
        f.write(f"Maximum SSIM : {max_ssim:.4f}\n\n")
        f.write(f"Successfully processed: {n}/{total}\n")
        f.write("========================================\n")
        if failed:
            f.write("\nFailed images:\n")
            for fname, reason in failed:
                f.write(f"  {fname}: {reason}\n")

    print(f"\nPer-image CSV    : {os.path.abspath(CSV_PATH)}")
    print(f"Summary text     : {os.path.abspath(SUMMARY_PATH)}")
    print(f"Enhanced images  : {os.path.abspath(ENHANCED_DIR)}")


if __name__ == "__main__":
    main()
