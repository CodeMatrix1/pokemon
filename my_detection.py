#!/usr/bin/env python3
"""
pokemon_yolo_pipeline.py (improved)

Now integrates both:
- instances_train.json (for YOLO training labels)
- train_prompts.json (for parsing HQ orders)
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Tuple
import cv2

import numpy as np
try:
    from ultralytics import YOLO
except Exception:
    YOLO = None

# ----------------------------------
# COCO -> YOLO conversion (unchanged)
# ----------------------------------
def coco_to_yolo_labels(coco_json_path: str, images_dir: str, out_labels_dir: str, classes: List[str]) -> None:
    coco = json.load(open(coco_json_path, 'r'))
    images = {img['id']: img for img in coco['images']}
    annotations = coco.get('annotations', [])
    catid2name = {c['id']: c['name'] for c in coco['categories']}
    name_to_idx = {name: i for i, name in enumerate(classes)}
    os.makedirs(out_labels_dir, exist_ok=True)
    anns_by_img = {}
    for ann in annotations:
        img_id = ann['image_id']
        anns_by_img.setdefault(img_id, []).append(ann)

    for img_id, img in images.items():
        fname = img['file_name']
        img_path = Path(images_dir) / fname
        if not img_path.exists():
            continue
        w, h = img['width'], img['height']
        out_txt = Path(out_labels_dir) / (Path(fname).stem + ".txt")
        lines = []
        for ann in anns_by_img.get(img_id, []):
            cat_name = catid2name.get(ann['category_id'], None)
            if cat_name is None or cat_name not in name_to_idx:
                continue
            cls_idx = name_to_idx[cat_name]
            x_min, y_min, bw, bh = ann['bbox']
            x_center = x_min + bw / 2.0
            y_center = y_min + bh / 2.0
            x_center /= w; y_center /= h; bw /= w; bh /= h
            lines.append(f"{cls_idx} {x_center:.6f} {y_center:.6f} {bw:.6f} {bh:.6f}")
        with open(out_txt, 'w') as f:
            f.write("\n".join(lines))

# ----------------------------------
# Detector class (Ultralytics inference)
# ----------------------------------
from ultralytics import YOLO

def train_yolo():
    # choose a base model
    model = YOLO("yolov8n.pt")  # nano version (<10MB, fast)
    
    # train on your dataset
    model.train(
        data="pokemon.yaml",
        epochs=50,
        imgsz=640,
        batch=16,
        name="pokemon_detector"
    )

    # after training, weights are in runs/detect/pokemon_detector/weights/best.pt
    return model


class PokemonDetectorUltralytics:
    def __init__(self, model_path: str, conf_thresh: float = 0.25, iou_thresh: float = 0.45):
        if YOLO is None:
            raise RuntimeError("Ultralytics not installed. pip install ultralytics")
        self.model = YOLO(model_path)
        self.conf_thresh = conf_thresh
        self.iou_thresh = iou_thresh
        self.names = self.model.names

    def predict(self, image_path: str) -> List[Dict]:
        results = self.model.predict(source=image_path, conf=self.conf_thresh, iou=self.iou_thresh, verbose=False)
        detections: List[Dict] = []
        if not results: return detections
        r = results[0]
        boxes = getattr(r, "boxes", None)
        if boxes is None: return detections
        for i in range(len(boxes)):
            xyxy = boxes[i].xyxy[0].cpu().numpy()
            conf = float(boxes[i].conf[0].cpu().numpy())
            cls = int(boxes[i].cls[0].cpu().numpy())
            x1, y1, x2, y2 = xyxy.tolist()
            x, y, w, h = int(x1), int(y1), int(x2 - x1), int(y2 - y1)
            cx, cy = int(x + w / 2), int(y + h / 2)
            species = self.names.get(cls, str(cls))
            detections.append({
                "species": species,
                "bbox": [x, y, w, h],
                "confidence": conf,
                "class_id": cls,
                "center": [cx, cy]
            })
        return detections

# ----------------------------------
# HQ Orders loader (NEW, uses train_prompts.json)
# ----------------------------------
def load_prompt_orders(prompts_path: str, image_id: str, all_species: List[str]) -> Dict:
    """
    Load HQ orders for given image_id from train_prompts.json
    Returns {"targets": [...], "protected": [...]}
    """
    with open(prompts_path, "r") as f:
        prompts = json.load(f)
    for entry in prompts:
        if entry["image_id"] == image_id:
            text = entry["prompt"].lower()
            targets, protected = [], []
            if "kill" in text:
                species = text.split("kill:")[1].strip()
                targets.append(species.capitalize())
                protected = [s for s in all_species if s not in targets]
            return {"targets": targets, "protected": protected}
    return {"targets": [], "protected": []}

# ----------------------------------
# Fusion: select targets given orders
# ----------------------------------
def fuse_with_orders(detections: List[Dict], orders_parsed: Dict[str, List[str]], safe_overlap_thresh=0.2, conf_threshold=0.4):
    targets = set([t.lower() for t in orders_parsed.get("targets", [])])
    protected = set([p.lower() for p in orders_parsed.get("protected", [])])
    prot_dets = [d for d in detections if d["species"].lower() in protected]
    cand_targets = [d for d in detections if d["species"].lower() in targets and d["confidence"] >= conf_threshold]

    def iou_bbox(a, b):
        ax1, ay1, aw, ah = a; bx1, by1, bw, bh = b
        ax2, ay2 = ax1+aw, ay1+ah; bx2, by2 = bx1+bw, by1+bh
        ix1, iy1 = max(ax1,bx1), max(ay1,by1)
        ix2, iy2 = min(ax2,bx2), min(ay2,by2)
        iw, ih = max(0, ix2-ix1), max(0, iy2-iy1)
        inter = iw*ih; union = aw*ah + bw*bh - inter
        return 0.0 if union==0 else inter/union

    safe_targets = []
    for cand in cand_targets:
        if all(iou_bbox(cand["bbox"], p["bbox"]) <= safe_overlap_thresh for p in prot_dets):
            safe_targets.append(cand)

    safe_targets.sort(key=lambda d: d["confidence"], reverse=True)
    return safe_targets, prot_dets

# ----------------------------------
# Demo pipeline
# ----------------------------------
def main_demo():
    classes = ["Pikachu", "Charizard", "Bulbasaur", "Mewtwo"]
    model_weights = "runs/detect/train/weights/best.pt"
    test_image = "img_00000.png"  # example test
    prompts_path = "train_prompts.json"

    if not os.path.exists(model_weights):
        print("Model weights not found. Please train YOLO first.")
        return

    detector = PokemonDetectorUltralytics(model_weights, conf_thresh=0.25)
    detections = detector.predict(test_image)
    print("Detections:", detections)

    # NEW: load orders for this image
    orders = load_prompt_orders(prompts_path, Path(test_image).name, classes)
    print("HQ Orders:", orders)

    targets, protected = fuse_with_orders(detections, orders)
    print("Targets selected:", targets)
    print("Protected:", protected)

if __name__ == "__main__":
    main_demo()
