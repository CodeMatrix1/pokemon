#!/usr/bin/env python3
"""
Pokemon: Tactical Strike - QA Validator & Metric Calculator
Python 3.9+. No external deps required.
Run: python tools/validator.py --ann path/to/instances_train.json --orders path/to/orders.json --pred path/to/predictions.csv --out reports/ --radii 6 8 10 12 15 20
"""

import argparse
import csv
import json
import math
import os
import sys
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Set, Any, Optional

# ---- Constants (spec-driven) ----
VALID_CLASS_IDS = {1, 2, 3, 4}  # Enforce 4 species only (why: spec restricts classes)
DEFAULT_RADII = [6, 8, 10, 12, 15, 20]  # Reasonable sweep since eval radius is unknown

# ---- Data types ----
BBox = Tuple[float, float, float, float]  # x, y, w, h
Point = Tuple[float, float]

# ---- Minimal rules-based orders parsing ----
def parse_hq_orders(text: str) -> Tuple[Set[int], Set[int]]:
    """
    Extract target and protected species ids from free-form orders.
    Why: Orders are ambiguous; we keep rules-based parsing deterministic for CI.
    """
    # Map canonical names to ids
    name2id = {
        "pikachu": 1, "charizard": 2, "bulbasaur": 3, "mewtwo": 4,
        # crude plurals
        "pikachus": 1, "charizards": 2, "bulbasaurs": 3, "mewtwos": 4,
    }

    text_l = text.lower()
    targets: Set[int] = set()
    protected: Set[int] = set()

    # Simple heuristics:
    # - phrases like "neutralize/kill/eliminate <species>" => targets
    # - phrases like "do not hit/avoid/protect <species>" => protected
    kill_triggers = ("neutralize", "eliminate", "kill", "take out", "engage", "target")
    protect_triggers = ("do not", "avoid", "protect", "preserve", "keep safe")

    # Collect mentioned species
    mentioned = {sid for name, sid in name2id.items() if name in text_l}

    # Assign based on local phrase windows
    for name, sid in name2id.items():
        if name not in text_l:
            continue
        idx = text_l.find(name)
        window = text_l[max(0, idx - 40): idx + 40]

        if any(k in window for k in kill_triggers):
            targets.add(sid)
        if any(p in window for p in protect_triggers):
            protected.add(sid)

    # Fallbacks: if text explicitly singles out one species as imminent threat
    if "imminent threat" in text_l or "priority target" in text_l:
        for sid in mentioned:
            # Bias toward Bulbasaur as in sample narrative, but only if present
            # (Why: provide deterministic behavior when ambiguity is high)
            pass

    # Ensure disjointness; targets win over protected in conflict (why: actionability)
    protected -= targets
    return targets, protected


# ---- Annotations I/O ----
def load_annotations(path: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Expect a COCO-like json or a simple structure:
    {
      "images": [{"id":"img_00000.png","width":W,"height":H}, ...],
      "annotations": [{"image_id":"img_00000.png","bbox":[x,y,w,h],"category_id":1}, ...]
    }
    Returns: dict image_id -> list of objects {bbox, cid, center}
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Handle both compact and COCO-like variants
    images = data.get("images", [])
    anns = data.get("annotations", [])

    id2shape = {}
    for im in images:
        iid = im.get("id") or im.get("file_name") or im.get("image_id")
        if not iid:
            continue
        id2shape[iid] = (im.get("width"), im.get("height"))

    by_img: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for a in anns:
        iid = a.get("image_id")
        bbox = a.get("bbox")
        cid = a.get("category_id")
        if iid is None or bbox is None or cid is None:
            continue
        x, y, w, h = map(float, bbox)
        cx, cy = x + w / 2.0, y + h / 2.0
        # Convert image_id to string to handle mixed types
        by_img[str(iid)].append({"bbox": (x, y, w, h), "cid": int(cid), "center": (cx, cy)})

    return by_img


# ---- Orders I/O ----
def load_orders(path: str) -> Dict[str, str]:
    """
    Expect:
      { "img_00000.png": "HQ text ...", "img_00001.png": "...", "_default": "..." }
    If per-image text missing, use "_default" if present.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {k: str(v) for k, v in data.items()}


# ---- Predictions I/O ----
def load_predictions_csv(path: str) -> Dict[str, List[Point]]:
    """
    CSV:
      image_id,points
      img_00000.png,"[[x1,y1],[x2,y2]]"
    """
    out: Dict[str, List[Point]] = {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if "image_id" not in reader.fieldnames or "points" not in reader.fieldnames:
            raise ValueError("CSV must contain 'image_id' and 'points' columns")
        for row in reader:
            iid = row["image_id"].strip()
            pts_str = row["points"].strip()
            try:
                pts = json.loads(pts_str)
                pts_t = []
                for p in pts:
                    if not (isinstance(p, (list, tuple)) and len(p) == 2):
                        continue
                    pts_t.append((float(p[0]), float(p[1])))
                out[iid] = pts_t
            except Exception as e:
                raise ValueError(f"Bad points JSON for {iid}: {e}")
    return out


# ---- Geometry / Matching ----
def euclid(a: Point, b: Point) -> float:
    dx, dy = a[0] - b[0], a[1] - b[1]
    return math.hypot(dx, dy)

def greedy_match(shots: List[Point], centers: List[Tuple[Point, int]], radius: float) -> Tuple[List[Tuple[int, int, float]], List[int], List[int]]:
    """
    Greedy nearest-neighbor one-to-one matching within radius.
    centers: list of (center_point, class_id)
    Returns:
      matches: list of (shot_idx, obj_idx, distance)
      missed_shots: indices of shots with no match
      unhit_objs: indices of objects with no match
    Why: Enforce one bullet ↔ one kill constraint deterministically.
    """
    if not shots or not centers:
        return [], list(range(len(shots))), list(range(len(centers)))

    obj_taken = [False] * len(centers)
    matches: List[Tuple[int, int, float]] = []

    # Precompute distances
    dists: List[Tuple[float, int, int]] = []  # (d, si, oi)
    for si, s in enumerate(shots):
        for oi, (cpt, _) in enumerate(centers):
            d = euclid(s, cpt)
            if d <= radius:
                dists.append((d, si, oi))
    dists.sort(key=lambda t: t[0])  # try closest pairs first

    shot_taken = [False] * len(shots)
    for d, si, oi in dists:
        if shot_taken[si] or obj_taken[oi]:
            continue
        shot_taken[si] = True
        obj_taken[oi] = True
        matches.append((si, oi, d))

    missed_shots = [i for i, used in enumerate(shot_taken) if not used]
    unhit_objs = [i for i, used in enumerate(obj_taken) if not used]
    return matches, missed_shots, unhit_objs


# ---- Scoring ----
def score_image(
    targets: Set[int],
    protected: Set[int],
    centers: List[Tuple[Point, int]],
    shots: List[Point],
    radius: float
) -> Dict[str, Any]:
    """
    Apply spec-like scoring.
    """
    matches, missed_shots, unhit_objs = greedy_match(shots, centers, radius)

    # Tally
    hit_by_species = Counter()
    collateral = 0
    correct = 0

    for si, oi, _ in matches:
        _, cid = centers[oi]
        if cid in targets:
            correct += 1
            hit_by_species[cid] += 1
        elif cid in protected:
            collateral += 1
        else:
            # neutral hit: neither rewarded nor penalized
            pass

    # All-enemy-eliminated bonus: if all target instances hit
    total_targets = sum(1 for _, cid in centers if cid in targets)
    all_enemy_down = (total_targets > 0) and (hit_by_species.total() == total_targets)
    bonus = 1 if all_enemy_down else 0

    # Miss penalty
    miss_penalty = (len(missed_shots) // 3) * 1

    total = correct + bonus - collateral - miss_penalty

    return {
        "correct": correct,
        "bonus_all_enemy_down": bonus,
        "collateral": collateral,
        "misses": len(missed_shots),
        "miss_penalty": miss_penalty,
        "total": total,
        "matched": len(matches),
        "unhit_objs": len(unhit_objs),
        "targets_present": total_targets,
        "targets_hit": hit_by_species.total(),
    }


# ---- Runner ----
def run_eval(ann_path: str, orders_path: str, pred_path: str, out_dir: str, radii: List[float]) -> None:
    os.makedirs(out_dir, exist_ok=True)

    anns = load_annotations(ann_path)
    orders = load_orders(orders_path)
    preds = load_predictions_csv(pred_path)

    image_ids = sorted(set(anns.keys()) | set(preds.keys()))
    if not image_ids:
        raise RuntimeError("No overlapping images between annotations and predictions")

    # Collect per-radius aggregate
    per_radius_agg: Dict[float, Dict[str, int]] = {r: Counter() for r in radii}

    # Per-image detailed rows
    detail_rows: List[Dict[str, Any]] = []

    for iid in image_ids:
        centers = [(obj["center"], obj["cid"]) for obj in anns.get(iid, [])]
        # Static check: only valid classes
        for _, cid in centers:
            if cid not in VALID_CLASS_IDS:
                raise ValueError(f"Invalid class id {cid} in annotations for {iid}")

        shots = preds.get(iid, [])

        # Per-image orders
        raw_order = orders.get(iid, orders.get("_default", ""))
        targets, protected = parse_hq_orders(raw_order)

        for r in radii:
            sc = score_image(targets, protected, centers, shots, r)
            # Aggregate
            per_radius_agg[r].update({
                "correct": sc["correct"],
                "bonus": sc["bonus_all_enemy_down"],
                "collateral": sc["collateral"],
                "miss_penalty_units": sc["miss_penalty"],
                "misses": sc["misses"],
                "total": sc["total"],
            })
            detail_rows.append({
                "image_id": iid,
                "radius": r,
                "correct": sc["correct"],
                "bonus_all_enemy_down": sc["bonus_all_enemy_down"],
                "collateral": sc["collateral"],
                "misses": sc["misses"],
                "miss_penalty": sc["miss_penalty"],
                "total": sc["total"],
                "targets_present": sc["targets_present"],
                "targets_hit": sc["targets_hit"],
            })

    # Write details CSV
    details_csv = os.path.join(out_dir, "per_image_details.csv")
    with open(details_csv, "w", newline="", encoding="utf-8") as f:
        fieldnames = list(detail_rows[0].keys())
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(detail_rows)

    # Write aggregate CSV
    agg_csv = os.path.join(out_dir, "aggregate_by_radius.csv")
    with open(agg_csv, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["radius", "correct", "bonus", "collateral", "misses", "miss_penalty_units", "total"]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in radii:
            agg = per_radius_agg[r]
            w.writerow({
                "radius": r,
                "correct": agg.get("correct", 0),
                "bonus": agg.get("bonus", 0),
                "collateral": agg.get("collateral", 0),
                "misses": agg.get("misses", 0),
                "miss_penalty_units": agg.get("miss_penalty_units", 0),
                "total": agg.get("total", 0),
            })

    # Markdown summary
    best_r = max(radii, key=lambda x: per_radius_agg[x].get("total", 0))
    summary_md = os.path.join(out_dir, "qa_summary.md")
    with open(summary_md, "w", encoding="utf-8") as f:
        f.write(f"# QA Summary\n\n")
        f.write(f"- Images evaluated: {len(image_ids)}\n")
        f.write(f"- Radii tested: {radii}\n")
        f.write(f"- Best radius by total score: **{best_r}**\n\n")
        f.write("## Next Actions\n")
        f.write("- Tune targeting point generator to be closer to instance centers to reduce miss penalty.\n")
        f.write("- Strengthen orders parser with NER/model fallback; add tests for protected-only scenes.\n")
        f.write("- Verify CSV formatting and per-image orders presence to avoid silent defaults.\n")

    print(f"[OK] Wrote:\n  {details_csv}\n  {agg_csv}\n  {summary_md}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ann", required=True, help="Path to instances_train.json-like annotations")
    parser.add_argument("--orders", required=True, help="Path to orders.json (per-image HQ text)")
    parser.add_argument("--pred", required=True, help="Path to predictions CSV")
    parser.add_argument("--out", required=True, help="Output directory for reports")
    parser.add_argument("--radii", nargs="+", type=float, default=DEFAULT_RADII, help="Radii to sweep")
    args = parser.parse_args()

    run_eval(args.ann, args.orders, args.pred, args.out, args.radii)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
