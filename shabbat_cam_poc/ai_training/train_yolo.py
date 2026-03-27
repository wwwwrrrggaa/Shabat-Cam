import os
import random
import shutil
import yaml
from pathlib import Path
from ultralytics import YOLO
from huggingface_hub import hf_hub_download

# --- 1. CONFIGURATION ---
BASE_DIR = Path(__file__).parent.parent.resolve()
# תיקון נתיב - וודא שהשם תואם בדיוק לתיקייה שלך (אותיות קטנות/גדולות)
DATA_DIR = BASE_DIR / "Blender_sim" / "training_data"
IMG_TRAIN = DATA_DIR / "images" / "train"
LBL_TRAIN = DATA_DIR / "labels" / "train"
IMG_VAL = DATA_DIR / "images" / "val"
LBL_VAL = DATA_DIR / "labels" / "val"

SPLIT_RATIO = 0.8


def setup_directories():
    IMG_VAL.mkdir(parents=True, exist_ok=True)
    LBL_VAL.mkdir(parents=True, exist_ok=True)


def perform_split():
    print("--- Performing Train/Val Split ---")
    all_images = list(IMG_TRAIN.glob("*.png"))

    if len(all_images) == 0:
        print(f"❌ No images found in: {IMG_TRAIN}")
        print("Check if your Blender output folder is correct.")
        return

    val_images = list(IMG_VAL.glob("*.png"))
    if len(val_images) > 0:
        print(f"Split already performed. Skipping.")
        return

    random.shuffle(all_images)
    split_index = int(len(all_images) * SPLIT_RATIO)
    val_subset = all_images[split_index:]

    for img_path in val_subset:
        label_path = LBL_TRAIN / (img_path.stem + ".txt")
        shutil.move(str(img_path), str(IMG_VAL / img_path.name))
        if label_path.exists():
            shutil.move(str(label_path), str(LBL_VAL / label_path.name))
    print(f"✅ Split complete.")


def create_yaml():
    yaml_path = DATA_DIR / "breech_obb.yaml"
    dataset_config = {
        "path": str(DATA_DIR),
        "train": "images/train",
        "val": "images/val",
        "names": {0: "Shell", 1: "Propellant"},
    }
    with open(yaml_path, "w") as f:
        yaml.dump(dataset_config, f, default_flow_style=False)
    return yaml_path


def train_model(yaml_path):
    print("\n--- Downloading YOLO26-S-OBB from Hugging Face ---")
    try:
        # הורדה ישירה מה-Repo ששלחת
        model_path = hf_hub_download(
            repo_id="openvision/yolo26-s-obb", filename="model.pt"
        )
        print(f"✅ Model downloaded to: {model_path}")
    except Exception as e:
        print(f"❌ Failed to download from HF: {e}")
        return

    model = YOLO(model_path)

    print("\n--- Starting Training ---")
    model.train(
        data=str(yaml_path),
        epochs=50,
        imgsz=640,
        batch=16,
        device=0,
        project="Breech_AI",
        name="yolo26_obb_v1",
        # Augmentations
        hsv_h=0.03,
        hsv_s=0.6,
        hsv_v=0.6,
        degrees=180.0,
        translate=0.2,
        scale=0.4,
        perspective=0.002,
        mosaic=1.0,
        mixup=0.15,
    )


if __name__ == "__main__":
    # וודא שהספרייה מותקנת: pip install huggingface_hub
    setup_directories()
    perform_split()
    y_file = create_yaml()
    train_model(y_file)