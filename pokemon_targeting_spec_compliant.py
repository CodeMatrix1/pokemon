#!/usr/bin/env python3
"""
Pokemon: Tactical Strike - Spec-Compliant Targeting System
Implements one-to-one matching, radius sweep, and spec-compliant scoring.
"""

import cv2
import json
import numpy as np
import math
from typing import List, Tuple, Dict, Set, Any, Optional
from collections import Counter

from pokemon_targeting_enhanced import EnhancedPokemonTargetingSystem


class SpecCompliantPokemonTargetingSystem(EnhancedPokemonTargetingSystem):
    """
    Spec-compliant Pokemon targeting system with one-to-one matching and scoring.
    """
    
    def __init__(self, detection_model_path: Optional[str] = None, default_radius: float = 12.0):
        """
        Initialize spec-compliant targeting system.
        
        :param detection_model_path: Path to detection model files
        :param default_radius: Default targeting radius for one-to-one matching
        """
        super().__init__(detection_model_path)
        self.default_radius = default_radius
        self.species_id_map = {
            "Pikachu": 1, "Charizard": 2, "Bulbasaur": 3, "Mewtwo": 4,
            "pikachu": 1, "charizard": 2, "bulbasaur": 3, "mewtwo": 4
        }
    
    def euclidean_distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """Calculate Euclidean distance between two points."""
        dx, dy = point1[0] - point2[0], point1[1] - point2[1]
        return math.hypot(dx, dy)
    
    def greedy_match_shots_to_targets(self, 
                                    shots: List[Tuple[float, float]], 
                                    targets: List[Tuple[Tuple[float, float], int]], 
                                    radius: float) -> Tuple[List[Tuple[int, int, float]], List[int], List[int]]:
        """
        Greedy nearest-neighbor one-to-one matching within radius.
        
        :param shots: List of shot coordinates
        :param targets: List of (target_center, species_id) tuples
        :param radius: Maximum distance for valid matches
        :return: (matches, missed_shots, unhit_targets)
        """
        if not shots or not targets:
            return [], list(range(len(shots))), list(range(len(targets)))
        
        # Precompute all valid distances
        valid_distances = []
        for shot_idx, shot in enumerate(shots):
            for target_idx, (target_center, _) in enumerate(targets):
                distance = self.euclidean_distance(shot, target_center)
                if distance <= radius:
                    valid_distances.append((distance, shot_idx, target_idx))
        
        # Sort by distance (closest first)
        valid_distances.sort(key=lambda x: x[0])
        
        # Greedy matching
        shot_taken = [False] * len(shots)
        target_taken = [False] * len(targets)
        matches = []
        
        for distance, shot_idx, target_idx in valid_distances:
            if not shot_taken[shot_idx] and not target_taken[target_idx]:
                shot_taken[shot_idx] = True
                target_taken[target_idx] = True
                matches.append((shot_idx, target_idx, distance))
        
        missed_shots = [i for i, taken in enumerate(shot_taken) if not taken]
        unhit_targets = [i for i, taken in enumerate(target_taken) if not taken]
        
        return matches, missed_shots, unhit_targets
    
    def calculate_spec_score(self, 
                           targets: Set[int], 
                           protected: Set[int], 
                           target_centers: List[Tuple[Tuple[float, float], int]], 
                           shots: List[Tuple[float, float]], 
                           radius: float) -> Dict[str, Any]:
        """
        Calculate spec-compliant scoring.
        
        Scoring rules:
        - +1 per correct hit on target species
        - +1 bonus if all enemy targets eliminated
        - -1 per hit on protected species
        - -1 per ⌊misses/3⌋
        
        :param targets: Set of target species IDs
        :param protected: Set of protected species IDs
        :param target_centers: List of (center, species_id) tuples
        :param shots: List of shot coordinates
        :param radius: Matching radius
        :return: Score breakdown
        """
        matches, missed_shots, unhit_targets = self.greedy_match_shots_to_targets(
            shots, target_centers, radius)
        
        # Tally results
        hit_by_species = Counter()
        collateral = 0
        correct = 0
        
        for shot_idx, target_idx, distance in matches:
            _, species_id = target_centers[target_idx]
            if species_id in targets:
                correct += 1
                hit_by_species[species_id] += 1
            elif species_id in protected:
                collateral += 1
        
        # All-enemy-eliminated bonus
        total_targets = sum(1 for _, species_id in target_centers if species_id in targets)
        all_enemy_down = (total_targets > 0) and (hit_by_species.total() == total_targets)
        bonus = 1 if all_enemy_down else 0
        
        # Miss penalty: ⌊misses/3⌋
        miss_penalty = len(missed_shots) // 3
        
        # Total score
        total = correct + bonus - collateral - miss_penalty
        
        return {
            "correct": correct,
            "bonus_all_enemy_down": bonus,
            "collateral": collateral,
            "misses": len(missed_shots),
            "miss_penalty": miss_penalty,
            "total": total,
            "matched": len(matches),
            "unhit_targets": len(unhit_targets),
            "targets_present": total_targets,
            "targets_hit": hit_by_species.total(),
            "hit_by_species": dict(hit_by_species)
        }
    
    def radius_sweep_analysis(self, 
                            targets: Set[int], 
                            protected: Set[int], 
                            target_centers: List[Tuple[Tuple[float, float], int]], 
                            shots: List[Tuple[float, float]], 
                            radii: List[float] = None) -> Dict[float, Dict[str, Any]]:
        """
        Perform radius sweep analysis.
        
        :param targets: Set of target species IDs
        :param protected: Set of protected species IDs
        :param target_centers: List of (center, species_id) tuples
        :param shots: List of shot coordinates
        :param radii: List of radii to test
        :return: Dictionary mapping radius to score results
        """
        if radii is None:
            radii = [6, 8, 10, 12, 15, 20]
        
        results = {}
        for radius in radii:
            score = self.calculate_spec_score(targets, protected, target_centers, shots, radius)
            results[radius] = score
        
        return results
    
    def generate_spec_compliant_targeting(self, 
                                        image_path: str, 
                                        mission_orders: str, 
                                        radius: float = None) -> Dict:
        """
        Generate spec-compliant targeting coordinates with scoring.
        
        :param image_path: Path to battlefield image
        :param mission_orders: HQ mission orders
        :param radius: Targeting radius (uses default if None)
        :return: Spec-compliant targeting result
        """
        if radius is None:
            radius = self.default_radius
        
        # Parse mission orders
        parsed_orders = self.parse_mission_orders(mission_orders)
        
        # Convert species names to IDs
        target_ids = {self.species_id_map[name] for name in parsed_orders["targets"] 
                     if name in self.species_id_map}
        protected_ids = {self.species_id_map[name] for name in parsed_orders["protected"] 
                        if name in self.species_id_map}
        
        # Detect Pokemon in image
        detected_pokemon = self.detector.detect_pokemon(image_path)
        
        # Convert detections to target centers with species IDs
        target_centers = []
        for detection in detected_pokemon:
            species_name = detection["species"]
            if species_name in self.species_id_map:
                species_id = self.species_id_map[species_name]
                x, y, w, h = detection["bounding_box"]
                center = (x + w / 2.0, y + h / 2.0)
                target_centers.append((center, species_id))
        
        # Generate shots (targeting coordinates for target species only)
        shots = []
        targeting_details = []
        
        for detection in detected_pokemon:
            species_name = detection["species"]
            if species_name in self.species_id_map:
                species_id = self.species_id_map[species_name]
                
                if species_id in target_ids:
                    x, y, w, h = detection["bounding_box"]
                    shot_coord = (x + w / 2.0, y + h / 2.0)
                    shots.append(shot_coord)
                    
                    targeting_details.append({
                        "species": species_name,
                        "species_id": species_id,
                        "coordinates": shot_coord,
                        "confidence": detection["confidence"],
                        "bounding_box": detection["bounding_box"],
                        "status": "target"
                    })
                elif species_id in protected_ids:
                    targeting_details.append({
                        "species": species_name,
                        "species_id": species_id,
                        "coordinates": None,
                        "confidence": detection["confidence"],
                        "bounding_box": detection["bounding_box"],
                        "status": "protected"
                    })
                else:
                    targeting_details.append({
                        "species": species_name,
                        "species_id": species_id,
                        "coordinates": None,
                        "confidence": detection["confidence"],
                        "bounding_box": detection["bounding_box"],
                        "status": "neutral"
                    })
        
        # Calculate spec-compliant score
        score = self.calculate_spec_score(target_ids, protected_ids, target_centers, shots, radius)
        
        # Perform radius sweep analysis
        radius_sweep = self.radius_sweep_analysis(target_ids, protected_ids, target_centers, shots)
        
        # Find optimal radius
        optimal_radius = max(radius_sweep.keys(), key=lambda r: radius_sweep[r]["total"])
        
        return {
            "coordinates": shots,
            "targeting_details": targeting_details,
            "mission_analysis": parsed_orders,
            "detection_results": detected_pokemon,
            "spec_score": score,
            "radius_sweep": radius_sweep,
            "optimal_radius": optimal_radius,
            "species_constraints": {
                "target_ids": target_ids,
                "protected_ids": protected_ids,
                "species_id_map": self.species_id_map
            }
        }
    
    def save_spec_compliant_report(self, 
                                 targeting_result: Dict, 
                                 output_file: str = "spec_compliant_report.json"):
        """
        Save spec-compliant mission report.
        
        :param targeting_result: Result from generate_spec_compliant_targeting
        :param output_file: Output file path
        """
        report = {
            "spec_compliance": {
                "one_to_one_matching": True,
                "radius_sweep_analysis": True,
                "spec_scoring": True,
                "species_constraints": True
            },
            "mission_summary": {
                "type": targeting_result["mission_analysis"]["mission_type"],
                "priority": targeting_result["mission_analysis"]["priority"],
                "targets": targeting_result["mission_analysis"]["targets"],
                "protected": targeting_result["mission_analysis"]["protected"],
                "targeting_coordinates": targeting_result["coordinates"]
            },
            "spec_score": targeting_result["spec_score"],
            "radius_analysis": {
                "tested_radii": list(targeting_result["radius_sweep"].keys()),
                "optimal_radius": targeting_result["optimal_radius"],
                "radius_scores": targeting_result["radius_sweep"]
            },
            "targeting_details": targeting_result["targeting_details"],
            "detection_results": targeting_result["detection_results"],
            "species_constraints": targeting_result["species_constraints"],
            "raw_orders": targeting_result["mission_analysis"]["raw_text"],
            "timestamp": self.get_timestamp()
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Spec-compliant report saved to {output_file}")
        
        # Print score summary
        score = targeting_result["spec_score"]
        print(f"\nSpec-Compliant Score Summary:")
        print(f"  Correct hits: {score['correct']}")
        print(f"  All enemies eliminated bonus: {score['bonus_all_enemy_down']}")
        print(f"  Collateral damage: {score['collateral']}")
        print(f"  Misses: {score['misses']}")
        print(f"  Miss penalty: {score['miss_penalty']}")
        print(f"  Total score: {score['total']}")
        print(f"  Optimal radius: {targeting_result['optimal_radius']}")


def main():
    """Demonstrate spec-compliant targeting system."""
    print("=== Spec-Compliant Pokemon Targeting System ===")
    print()
    
    # Initialize spec-compliant system
    system = SpecCompliantPokemonTargetingSystem()
    
    # Example mission orders
    mission_orders = """
    URGENT: HQ has detected unusual Bulbasaur activity in Sector 7. Field sensors logged anomalous behavior that suggests an imminent threat.
    Remember there are Pikachu and Charizard nearby — take care not to draw them into combat. 
    You are to neutralize the bulbasaurs immediately. This is a high-priority elimination mission.
    """
    
    # Process mission
    image_path = "battlefield_image.png"
    print("Processing spec-compliant mission orders...")
    print()
    
    targeting_result = system.generate_spec_compliant_targeting(image_path, mission_orders)
    
    print(f"Mission Analysis:")
    print(f"  Type: {targeting_result['mission_analysis']['mission_type']}")
    print(f"  Priority: {targeting_result['mission_analysis']['priority']}")
    print(f"  Target species: {targeting_result['mission_analysis']['targets']}")
    print(f"  Protected species: {targeting_result['mission_analysis']['protected']}")
    print(f"  Targeting coordinates: {targeting_result['coordinates']}")
    
    # Save spec-compliant report
    system.save_spec_compliant_report(targeting_result)
    
    # Show radius sweep results
    print(f"\nRadius Sweep Analysis:")
    for radius, score in targeting_result['radius_sweep'].items():
        print(f"  Radius {radius}: Score {score['total']} (Hits: {score['correct']}, Misses: {score['misses']})")
    
    print("\nSpec-compliant mission analysis complete!")


if __name__ == "__main__":
    main()

