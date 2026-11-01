import os
import random
import csv
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Set up paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DETECTION_DIR = BASE_DIR / "training" / "datasets" / "detection"
RECOGNITION_DIR = BASE_DIR / "training" / "datasets" / "recognition"
REPORTS_DIR = BASE_DIR / "training" / "reports"

os.makedirs(DETECTION_DIR / "images" / "train", exist_ok=True)
os.makedirs(DETECTION_DIR / "images" / "val", exist_ok=True)
os.makedirs(DETECTION_DIR / "images" / "test", exist_ok=True)
os.makedirs(DETECTION_DIR / "labels" / "train", exist_ok=True)
os.makedirs(DETECTION_DIR / "labels" / "val", exist_ok=True)
os.makedirs(DETECTION_DIR / "labels" / "test", exist_ok=True)
os.makedirs(RECOGNITION_DIR / "images", exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# Sample Ground Truth Indian Plates
INDIAN_PLATES = [
    # Standard Private (White)
    ("DL01AB1234", "WHITE"),
    ("MH12DE1433", "WHITE"),
    ("KA05MG8821", "WHITE"),
    ("HR26DK8888", "WHITE"),
    ("UP16CD5566", "WHITE"),
    ("TN07BK3341", "WHITE"),
    ("GJ01EF9922", "WHITE"),
    ("RJ14GH7711", "WHITE"),
    ("WB02IJ3344", "WHITE"),
    ("KL07KL5566", "WHITE"),
    ("AP09MN7890", "WHITE"),
    ("TS08OP1122", "WHITE"),
    ("MP04QR4455", "WHITE"),
    ("CH01ST6677", "WHITE"),
    ("PB10UV8899", "WHITE"),

    # EV Plates (Green background)
    ("MH02EV1001", "GREEN"),
    ("DL03EV2020", "GREEN"),
    ("KA03EV3344", "GREEN"),
    ("TS09EV5566", "GREEN"),
    ("TN09EV7788", "GREEN"),
    ("UP14EV9900", "GREEN"),

    # Commercial (Yellow background)
    ("DL1TA4500", "YELLOW"),
    ("MH01TC8899", "YELLOW"),
    ("KA04TB1234", "YELLOW"),
    ("HR55T9999", "YELLOW"),

    # Bharat (BH) Series
    ("22BH1029AB", "WHITE"),
    ("23BH4567ZZ", "WHITE"),
    ("21BH8812CD", "WHITE"),
    ("24BH3344EF", "WHITE"),

    # Vintage / Additional States
    ("DL8CAF5032", "WHITE"),
    ("MH04FA7788", "WHITE"),
    ("KA01AB9999", "WHITE"),
    ("TN22AA1001", "WHITE"),
    ("UP32EF9090", "WHITE"),
    ("HR51AB2020", "WHITE"),
    ("GJ05CD6789", "WHITE"),
    ("RJ02EF1111", "WHITE"),
    ("OD02GH3333", "WHITE"),
    ("JH01IJ5555", "WHITE"),
    ("BR01KL7777", "WHITE"),
    ("AS01MN9999", "WHITE"),
]

def render_plate_image(plate_text: str, plate_type: str = "WHITE") -> Image.Image:
    """Renders a realistic rectangular Indian number plate."""
    w, h = 340, 80
    bg_color = (255, 255, 255) if plate_type == "WHITE" else ((34, 139, 34) if plate_type == "GREEN" else (255, 215, 0))
    text_color = (255, 255, 255) if plate_type == "GREEN" else (15, 15, 15)
    border_color = (15, 15, 15)

    img = Image.new("RGB", (w, h), bg_color)
    draw = ImageDraw.Draw(img)

    # Outer border
    draw.rectangle([2, 2, w - 3, h - 3], outline=border_color, width=4)

    # Blue HSRP strip on the left with 'IND'
    draw.rectangle([4, 4, 38, h - 5], fill=(0, 51, 153))
    # Small chakra circle
    draw.ellipse([14, 18, 28, 32], outline=(255, 215, 0), width=2)

    # Format plate text with spaced presentation e.g. DL 01 AB 1234
    formatted = plate_text
    if len(plate_text) == 10 and not plate_text.startswith("2"):
        formatted = f"{plate_text[:2]} {plate_text[2:4]} {plate_text[4:6]} {plate_text[6:]}"
    elif plate_text.startswith("2") and "BH" in plate_text:
        formatted = f"{plate_text[:2]} BH {plate_text[4:8]} {plate_text[8:]}"

    # Try loading a clear font, otherwise use default
    font = ImageFont.load_default()
    # Draw IND letters on blue strip
    draw.text((12, 42), "IND", fill=(255, 255, 255), font=font)

    # Plate text
    draw.text((55, 24), formatted, fill=text_color, font=font)

    return img

def render_vehicle_frame_with_plate(plate_img: Image.Image) -> tuple[Image.Image, list[float]]:
    """
    Simulates a full camera scene containing a vehicle with the number plate.
    Returns: (scene_img, yolo_bbox) where bbox is [x_center, y_center, width, height] normalized.
    """
    scene_w, scene_h = 640, 480
    # Background vehicle hood/bumper colors
    car_colors = [(40, 40, 45), (180, 180, 190), (120, 20, 20), (20, 40, 90), (220, 220, 225)]
    car_bg = random.choice(car_colors)

    scene = Image.new("RGB", (scene_w, scene_h), car_bg)
    draw = ImageDraw.Draw(scene)

    # Vehicle grille and lines
    draw.rectangle([60, 80, scene_w - 60, scene_h - 40], fill=(25, 25, 28))
    for y in range(120, scene_h - 120, 28):
        draw.line([(80, y), (scene_w - 80, y)], fill=(60, 60, 65), width=3)

    # Random placement of plate on the bumper area
    pw, ph = plate_img.size
    px = random.randint(scene_w // 2 - 190, scene_w // 2 - 150)
    py = random.randint(scene_h // 2 + 30, scene_h // 2 + 70)

    scene.paste(plate_img, (px, py))

    # Normalized YOLO coordinates (class 0: number_plate)
    x_center = (px + pw / 2.0) / float(scene_w)
    y_center = (py + ph / 2.0) / float(scene_h)
    norm_w = pw / float(scene_w)
    norm_h = ph / float(scene_h)

    yolo_bbox = [x_center, y_center, norm_w, norm_h]
    return scene, yolo_bbox

def main():
    print("=== PREPARING DATASETS FOR SMARTPARK AI ===")
    all_plates = INDIAN_PLATES.copy()
    random.seed(42)
    random.shuffle(all_plates)

    # 70% train, 20% val, 10% test split
    total = len(all_plates)
    n_train = int(total * 0.70)
    n_val = int(total * 0.20)
    n_test = total - n_train - n_val

    splits = {
        "train": all_plates[:n_train],
        "val": all_plates[n_train:n_train + n_val],
        "test": all_plates[n_train + n_val:]
    }

    # Labels for recognition
    rec_records = []

    for split_name, items in splits.items():
        print(f"Generating {split_name} set ({len(items)} samples)...")
        for idx, (reg, ptype) in enumerate(items):
            plate_img = render_plate_image(reg, ptype)

            # 1. Save recognition cropped plate
            rec_filename = f"plate_{split_name}_{idx:03d}_{reg}.jpg"
            rec_path = RECOGNITION_DIR / "images" / rec_filename
            plate_img.save(rec_path)
            rec_records.append({
                "split": split_name,
                "image_path": f"images/{rec_filename}",
                "registration_number": reg,
                "plate_type": ptype
            })

            # 2. Render vehicle scene for detection
            scene_img, yolo_box = render_vehicle_frame_with_plate(plate_img)
            det_img_name = f"vehicle_{split_name}_{idx:03d}_{reg}.jpg"
            det_label_name = f"vehicle_{split_name}_{idx:03d}_{reg}.txt"

            det_img_path = DETECTION_DIR / "images" / split_name / det_img_name
            det_label_path = DETECTION_DIR / "labels" / split_name / det_label_name

            scene_img.save(det_img_path)

            # Write YOLO label: class x_center y_center width height
            with open(det_label_path, "w") as f:
                f.write(f"0 {yolo_box[0]:.6f} {yolo_box[1]:.6f} {yolo_box[2]:.6f} {yolo_box[3]:.6f}\n")

    # Save recognition CSVs
    labels_csv_path = RECOGNITION_DIR / "labels.csv"
    with open(labels_csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["split", "image_path", "registration_number", "plate_type"])
        writer.writeheader()
        writer.writerows(rec_records)

    for split_name in ["train", "val", "test"]:
        split_csv = RECOGNITION_DIR / f"{split_name}.csv"
        subset = [r for r in rec_records if r["split"] == split_name]
        with open(split_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["image_path", "registration_number", "plate_type"])
            writer.writeheader()
            for row in subset:
                writer.writerow({
                    "image_path": row["image_path"],
                    "registration_number": row["registration_number"],
                    "plate_type": row["plate_type"]
                })

    # Create data.yaml for YOLO training
    yaml_content = f"""# SmartPark AI Number Plate Detection Dataset
path: {DETECTION_DIR.as_posix()}
train: images/train
val: images/val
test: images/test

names:
  0: number_plate
"""
    with open(DETECTION_DIR / "data.yaml", "w") as f:
        f.write(yaml_content)

    print("Datasets prepared successfully!")
    print(f"Total detection images: {total}")
    print(f"Total recognition crops: {total}")
    print(f"YOLO data.yaml created at {DETECTION_DIR / 'data.yaml'}")

if __name__ == "__main__":
    main()

