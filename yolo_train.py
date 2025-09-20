#!/usr/bin/env python3
"""
YOLOv8 pipeline restricted to only training and testing.
Assumes dataset is already converted into YOLO format with:
- images/train, images/val
- labels/train, labels/val
- pokemon.yaml
"""

import os
from ultralytics import YOLO

def train_yolo(
    yaml_path="dataset_yolo/pokemon.yaml",
    model_size="yolov8n.pt",
    epochs=50,
    imgsz=640,
    batch=16,
    name="pokemon_detector"
):
    """
    Train YOLOv8 on your dataset.
    """
    model = YOLO(model_size)
    model.train(
        data=yaml_path,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        name=name
    )
    return model

def test_yolo(weights_path="runs/detect/pokemon_detector3/weights/best.pt",
              yaml_path="dataset_yolo/pokemon.yaml"):
    """
    Test YOLOv8 on validation set.
    """
    if not os.path.exists(weights_path):
        raise FileNotFoundError(f"❌ Trained weights not found at {weights_path}")

    model = YOLO(weights_path)
    results = model.val(data=yaml_path)
    return results

if __name__ == "__main__":
    # 1. Train

    # 2. Test (on val set)
    print("🔎 Evaluating YOLOv8 on validation set...")
    results = test_yolo()
    print("✅ Done. Metrics:", results)
