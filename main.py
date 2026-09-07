import os
import cv2
import config

from modules.image_io      import load_image
from modules.preprocessing import preprocess
from modules.gamma         import gamma_correction
from modules.clahe         import apply_clahe
from modules.bilateral     import bilateral_filter
from modules.color_restore import restore_color
from modules.evaluation    import evaluate, export_ablation_study
from utils.save_images     import save

SUPPORTED_EXT = {".png", ".jpg", ".jpeg"}

STAGES = [
    "Raw Low-Light",
    "After Gamma",
    "After CLAHE",
    "After Bilateral",
    "After Color Restore",
]

# accumulate per-stage scores across all images
stage_psnr = {s: [] for s in STAGES}
stage_ssim = {s: [] for s in STAGES}

low_files = sorted([
    f for f in os.listdir(config.DATASET_LOW)
    if os.path.splitext(f)[1].lower() in SUPPORTED_EXT
])

if not low_files:
    print(f"No images found in: {config.DATASET_LOW}")
    exit()

col = 22
print(f"\n{'Ablation Analysis — LOL eval15':^{5 + col + (10+9)*5}}")
print("=" * (5 + col + (10 + 9) * 5))
header = f"{'Image':<{col}}" + "".join(
    f"{'PSNR':>10}{'SSIM':>9}" for _ in STAGES
)
stage_header = f"{'':<{col}}" + "".join(
    f"{s:>19}" for s in STAGES
)
print(stage_header)
print(header)
print("-" * (col + (10 + 9) * 5))

for filename in low_files:
    low_path  = os.path.join(config.DATASET_LOW,  filename)
    high_path = os.path.join(config.DATASET_HIGH, filename)

    if not os.path.isfile(high_path):
        print(f"[ERROR] Ground-truth not found for {filename} — skipping.")
        continue

    try:
        low_image = load_image(low_path)
        gt_image  = load_image(high_path)
    except Exception as e:
        print(f"[ERROR] Could not load {filename}: {e} — skipping.")
        continue

    # ------------------------------------------------------------------ #
    # Run pipeline stage by stage
    # ------------------------------------------------------------------ #
    s0 = preprocess(low_image)                  # Raw low-light (baseline)
    s1 = gamma_correction(s0, config.GAMMA)     # + Gamma Correction
    s2 = apply_clahe(s1)                        # + CLAHE
    s3 = bilateral_filter(s2)                   # + Bilateral Filter
    s4 = restore_color(s3)                      # + Color Restoration (final)

    # save final enhanced image
    name = os.path.splitext(filename)[0]
    save(s4, f"{name}_enhanced.jpg")

    # ------------------------------------------------------------------ #
    # Evaluate each stage against ground-truth
    # ------------------------------------------------------------------ #
    results = {}
    for stage, img in zip(STAGES, [s0, s1, s2, s3, s4]):
        gt = gt_image
        if img.shape != gt.shape:
            gt = cv2.resize(gt, (img.shape[1], img.shape[0]),
                            interpolation=cv2.INTER_AREA)
        psnr, ssim = evaluate(gt, img)
        results[stage] = (psnr, ssim)
        stage_psnr[stage].append(psnr)
        stage_ssim[stage].append(ssim)

    row = f"{filename:<{col}}"
    for s in STAGES:
        p, si = results[s]
        row += f"{p:>10.2f}{si:>9.4f}"
    print(row)

# ------------------------------------------------------------------ #
# Mean across all images per stage
# ------------------------------------------------------------------ #
n = len(low_files)
print("=" * (col + (10 + 9) * 5))
print(f"\n{'Mean PSNR and SSIM per Stage (across all images)':^{col + (10+9)*5}}\n")
print(f"{'Stage':<25} {'Mean PSNR (dB)':>15} {'Mean SSIM':>12}")
print("-" * 54)
for s in STAGES:
    if stage_psnr[s]:
        mp = sum(stage_psnr[s]) / len(stage_psnr[s])
        ms = sum(stage_ssim[s]) / len(stage_ssim[s])
        print(f"{s:<25} {mp:>15.4f} {ms:>12.4f}")
print("-" * 54)
print(f"\nImages evaluated: {len(stage_psnr[STAGES[0]])} / {n}")

# ------------------------------------------------------------------ #
# Export ablation study — CSV + Markdown table
# ------------------------------------------------------------------ #
ablation_data = {
    s: (
        sum(stage_psnr[s]) / len(stage_psnr[s]),
        sum(stage_ssim[s]) / len(stage_ssim[s])
    )
    for s in STAGES if stage_psnr[s]
}

export_ablation_study(ablation_data, output_path="output/ablation_study.csv")
