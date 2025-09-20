#!/usr/bin/env python3
"""
convert_coco_to_yolo_verbose.py

Verbose COCO -> YOLO converter with diagnostics (Windows-friendly).

Usage (edit paths at bottom or call functions from another script).
"""

import os
import json
import random
import shutil
from pathlib import Path
from collections import defaultdict

# EDIT THIS to the classes you expect YOLO to learn (order matters)
CLASSES = ["Pikachu", "Charizard", "Bulbasaur", "Mewtwo"]

def coco_to_yolo_bbox(bbox, img_w, img_h):
    x_min, y_min, w, h = bbox
    x_center = x_min + w / 2.0
    y_center = y_min + h / 2.0
    return [x_center / img_w, y_center / img_h, w / img_w, h / img_h]

def smart_map_categories(coco_categories, target_classes):
    """
    Try to map COCO category names to target_classes.
    Returns dict cat_id -> cls_idx and a list of unmapped categories.
    """
    catid_to_name = {c['id']: c['name'] for c in coco_categories}
    mapping = {}
    unmapped = {}

    lower_targets = [t.lower() for t in target_classes]

    for cid, cname in catid_to_name.items():
        cname_l = cname.lower()
        mapped_idx = None

        # exact match
        for i, t in enumerate(lower_targets):
            if cname_l == t:
                mapped_idx = i
                break

        # substring / partial match (e.g., "bulbasaur_sprite" -> "Bulbasaur")
        if mapped_idx is None:
            for i, t in enumerate(lower_targets):
                if t in cname_l or cname_l in t:
                    mapped_idx = i
                    break

        if mapped_idx is not None:
            mapping[cid] = mapped_idx
        else:
            unmapped[cid] = cname

    return mapping, unmapped

def convert_coco_verbose(coco_json_path, images_dir, output_dir, val_split=0.2, seed=42):
    random.seed(seed)
    coco_json_path = Path(coco_json_path)
    images_dir = Path(images_dir)
    output_dir = Path(output_dir)

    if not coco_json_path.exists():
        raise FileNotFoundError(f"COCO JSON not found: {coco_json_path}")
    if not images_dir.exists():
        raise FileNotFoundError(f"Images dir not found: {images_dir}")

    coco = json.load(open(coco_json_path, 'r', encoding='utf-8'))
    images = {img['id']: img for img in coco.get('images', [])}
    annotations = coco.get('annotations', [])
    categories = coco.get('categories', [])

    print("=== COCO categories found ===")
    for c in categories:
        print(f"  id={c['id']:>3}  name='{c['name']}'")
    print("=============================\n")

    mapping, unmapped = smart_map_categories(categories, CLASSES)
    if unmapped:
        print("⚠️  Some COCO categories could not be auto-mapped to your CLASSES:")
        for cid, cname in unmapped.items():
            print(f"   - {cid}: '{cname}'")
        print("→ These annotations will be skipped unless you add a mapping or change CLASSES.\n")
    else:
        print("✅ All COCO categories mapped to CLASSES.\n")

    print("Category mapping (COCO id -> class index):")
    for cid, idx in mapping.items():
        print(f"  {cid} -> {idx} ('{CLASSES[idx]}')")
    print()

    # make output structure
    imgs_out = output_dir / "images"
    labels_out = output_dir / "labels"
    for s in ("train", "val"):
        (imgs_out / s).mkdir(parents=True, exist_ok=True)
        (labels_out / s).mkdir(parents=True, exist_ok=True)

    # group annotations by image_id
    anns_by_img = defaultdict(list)
    for ann in annotations:
        anns_by_img[ann['image_id']].append(ann)

    img_ids = list(images.keys())
    random.shuffle(img_ids)
    n_val = int(len(img_ids) * val_split)
    val_ids = set(img_ids[:n_val])

    counts = {
        "images_total": 0,
        "images_copied": 0,
        "labels_written": 0,
        "labels_empty": 0,
        "annotations_total": len(annotations),
        "annotations_mapped": 0,
        "annotations_unmapped": 0
    }
    per_class_counts = [0] * len(CLASSES)

    for img_id, img_info in images.items():
        counts["images_total"] += 1
        fname = img_info["file_name"]
        src_img = images_dir / fname
        split = "val" if img_id in val_ids else "train"
        dst_img = imgs_out / split / fname

        if not src_img.exists():
            print(f"⚠️  Image file missing on disk: {src_img}  (image id {img_id}) -> skipping image.")
            # still create an empty label file so file counts match (optional)
            (labels_out / split / (Path(fname).stem + ".txt")).write_text("")
            counts["labels_empty"] += 1
            continue

        shutil.copy(str(src_img), str(dst_img))
        counts["images_copied"] += 1

        # collect annotations for this image
        anns = anns_by_img.get(img_id, [])
        lines = []
        for ann in anns:
            cid = ann['category_id']
            if cid not in mapping:
                counts["annotations_unmapped"] += 1
                continue
            cls_idx = mapping[cid]
            x_center, y_center, w, h = coco_to_yolo_bbox(ann['bbox'], img_info['width'], img_info['height'])
            lines.append(f"{cls_idx} {x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f}")
            counts["annotations_mapped"] += 1
            per_class_counts[cls_idx] += 1

        label_file = labels_out / split / (Path(fname).stem + ".txt")
        # write lines even if empty (YOLO expects empty file if no objects)
        label_file.write_text("\n".join(lines))
        counts["labels_written"] += 1
        if len(lines) == 0:
            counts["labels_empty"] += 1

    # report
    print("\n=== Conversion summary ===")
    print(f"Total images in COCO JSON: {counts['images_total']}")
    print(f"Images copied to output: {counts['images_copied']}")
    print(f"Total annotations in COCO: {counts['annotations_total']}")
    print(f"Mapped annotations written: {counts['annotations_mapped']}")
    print(f"Unmapped annotations skipped: {counts['annotations_unmapped']}")
    print(f"Label files written: {counts['labels_written']} (empty: {counts['labels_empty']})")
    print("Per-class annotation counts:")
    for i, c in enumerate(CLASSES):
        print(f"  {i} '{c}': {per_class_counts[i]}")
    print("===========================")

    # create dataset yaml
    yaml_path = output_dir / "pokemon.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write(f"path: {str(output_dir.resolve())}\n")
        f.write("train: images/train\n")
        f.write("val: images/val\n")
        f.write(f"nc: {len(CLASSES)}\n")
        f.write(f"names: {CLASSES}\n")
    print(f"Dataset yaml written to: {yaml_path}\n")

if __name__ == "__main__":
    # Edit these paths for your Windows environment
    coco_json = r"dataset\annotations\instances_train.json"
    images_dir = r"dataset\images"
    output_dir = r"dataset_yolo"

    convert_coco_verbose(coco_json, images_dir, output_dir)
    # helpful hint if many unmapped
