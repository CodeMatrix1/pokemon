#!/usr/bin/env python3
"""
Test suite for one-to-one matching and radius sweep behavior.
Tests the greedy matching algorithm and radius sensitivity analysis.
"""

import unittest
import sys
import os
import math
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))

from validator import greedy_match, euclid, score_image


class TestMatchingAndRadius(unittest.TestCase):
    """Test one-to-one matching and radius sweep behavior."""
    
    def test_euclidean_distance(self):
        """Test Euclidean distance calculation."""
        # Test basic distance calculation
        point1 = (0.0, 0.0)
        point2 = (3.0, 4.0)
        expected_distance = 5.0  # 3-4-5 triangle
        
        self.assertAlmostEqual(euclid(point1, point2), expected_distance, places=5)
        
        # Test distance to self
        self.assertAlmostEqual(euclid(point1, point1), 0.0, places=5)
        
        # Test negative coordinates
        point3 = (-3.0, -4.0)
        self.assertAlmostEqual(euclid(point1, point3), expected_distance, places=5)
    
    def test_greedy_matching_basic(self):
        """Test basic greedy matching functionality."""
        shots = [(10.0, 10.0), (50.0, 50.0)]
        centers = [((15.0, 15.0), 1), ((45.0, 45.0), 2)]  # (point, class_id)
        radius = 10.0
        
        matches, missed_shots, unhit_objs = greedy_match(shots, centers, radius)
        
        # Should match both shots to objects
        self.assertEqual(len(matches), 2)
        self.assertEqual(len(missed_shots), 0)
        self.assertEqual(len(unhit_objs), 0)
        
        # Check that each shot is matched to closest object
        self.assertEqual(matches[0][0], 0)  # shot 0
        self.assertEqual(matches[0][1], 0)  # object 0
        self.assertEqual(matches[1][0], 1)  # shot 1
        self.assertEqual(matches[1][1], 1)  # object 1
    
    def test_greedy_matching_with_misses(self):
        """Test greedy matching when shots miss targets."""
        shots = [(10.0, 10.0), (100.0, 100.0)]  # Second shot is far away
        centers = [((15.0, 15.0), 1)]  # Only one target
        radius = 10.0
        
        matches, missed_shots, unhit_objs = greedy_match(shots, centers, radius)
        
        # Should match one shot, miss one shot
        self.assertEqual(len(matches), 1)
        self.assertEqual(len(missed_shots), 1)
        self.assertEqual(len(unhit_objs), 0)
        
        # First shot should match, second should miss
        self.assertEqual(matches[0][0], 0)
        self.assertEqual(missed_shots[0], 1)
    
    def test_greedy_matching_with_unhit_objects(self):
        """Test greedy matching when objects are not hit."""
        shots = [(10.0, 10.0)]  # Only one shot
        centers = [((15.0, 15.0), 1), ((50.0, 50.0), 2)]  # Two targets
        radius = 10.0
        
        matches, missed_shots, unhit_objs = greedy_match(shots, centers, radius)
        
        # Should match one shot, leave one object unhit
        self.assertEqual(len(matches), 1)
        self.assertEqual(len(missed_shots), 0)
        self.assertEqual(len(unhit_objs), 1)
        
        # First shot should match closest object
        self.assertEqual(matches[0][0], 0)
        self.assertEqual(matches[0][1], 0)
        self.assertEqual(unhit_objs[0], 1)
    
    def test_greedy_matching_radius_sensitivity(self):
        """Test how matching changes with different radii."""
        shots = [(10.0, 10.0), (20.0, 20.0)]
        centers = [((15.0, 15.0), 1), ((25.0, 25.0), 2)]
        
        # Test with small radius (should miss both)
        matches_small, missed_small, unhit_small = greedy_match(shots, centers, 2.0)
        self.assertEqual(len(matches_small), 0)
        self.assertEqual(len(missed_small), 2)
        self.assertEqual(len(unhit_small), 2)
        
        # Test with medium radius (should match one)
        matches_medium, missed_medium, unhit_medium = greedy_match(shots, centers, 8.0)
        self.assertEqual(len(matches_medium), 1)
        self.assertEqual(len(missed_medium), 1)
        self.assertEqual(len(unhit_medium), 1)
        
        # Test with large radius (should match both)
        matches_large, missed_large, unhit_large = greedy_match(shots, centers, 15.0)
        self.assertEqual(len(matches_large), 2)
        self.assertEqual(len(missed_large), 0)
        self.assertEqual(len(unhit_large), 0)
    
    def test_one_to_one_constraint(self):
        """Test that one-to-one constraint is enforced."""
        shots = [(10.0, 10.0), (12.0, 12.0)]  # Two shots close together
        centers = [((15.0, 15.0), 1)]  # Only one target
        radius = 10.0
        
        matches, missed_shots, unhit_objs = greedy_match(shots, centers, radius)
        
        # Should only match one shot to the target (one-to-one constraint)
        self.assertEqual(len(matches), 1)
        self.assertEqual(len(missed_shots), 1)
        self.assertEqual(len(unhit_objs), 0)
        
        # The closer shot should be matched
        matched_shot_idx = matches[0][0]
        missed_shot_idx = missed_shots[0]
        self.assertNotEqual(matched_shot_idx, missed_shot_idx)
    
    def test_radius_sweep_behavior(self):
        """Test behavior across a range of radii."""
        shots = [(10.0, 10.0), (20.0, 20.0), (30.0, 30.0)]
        centers = [((15.0, 15.0), 1), ((25.0, 25.0), 2), ((35.0, 35.0), 3)]
        
        radii = [5.0, 8.0, 10.0, 12.0, 15.0, 20.0]
        match_counts = []
        
        for radius in radii:
            matches, _, _ = greedy_match(shots, centers, radius)
            match_counts.append(len(matches))
        
        # Match count should be non-decreasing with radius
        for i in range(1, len(match_counts)):
            self.assertLessEqual(match_counts[i-1], match_counts[i],
                               f"Match count should not decrease with increasing radius at {radii[i]}")
    
    def test_scoring_system_basic(self):
        """Test basic scoring system functionality."""
        targets = {1, 3}  # Bulbasaur and Mewtwo are targets
        protected = {2}   # Charizard is protected
        centers = [((15.0, 15.0), 1), ((25.0, 25.0), 2), ((35.0, 35.0), 3)]
        shots = [(15.0, 15.0), (25.0, 25.0), (35.0, 35.0)]
        radius = 5.0
        
        score = score_image(targets, protected, centers, shots, radius)
        
        # Should have 2 correct hits (targets), 1 collateral (protected)
        self.assertEqual(score["correct"], 2)
        self.assertEqual(score["collateral"], 1)
        self.assertEqual(score["misses"], 0)
        self.assertEqual(score["bonus_all_enemy_down"], 1)  # All targets hit
        self.assertEqual(score["miss_penalty"], 0)
        
        # Total score: +2 (correct) +1 (bonus) -1 (collateral) -0 (miss penalty) = 2
        self.assertEqual(score["total"], 2)
    
    def test_miss_penalty_calculation(self):
        """Test miss penalty calculation (⌊misses/3⌋)."""
        targets = {1}
        protected = set()
        centers = [((15.0, 15.0), 1)]
        radius = 5.0
        
        # Test with 0, 1, 2 misses (no penalty)
        for misses in range(3):
            shots = [(100.0, 100.0)] * misses  # All shots miss
            score = score_image(targets, protected, centers, shots, radius)
            self.assertEqual(score["misses"], misses)
            self.assertEqual(score["miss_penalty"], 0)
        
        # Test with 3 misses (penalty of 1)
        shots = [(100.0, 100.0)] * 3
        score = score_image(targets, protected, centers, shots, radius)
        self.assertEqual(score["misses"], 3)
        self.assertEqual(score["miss_penalty"], 1)
        
        # Test with 5 misses (penalty of 1)
        shots = [(100.0, 100.0)] * 5
        score = score_image(targets, protected, centers, shots, radius)
        self.assertEqual(score["misses"], 5)
        self.assertEqual(score["miss_penalty"], 1)
        
        # Test with 6 misses (penalty of 2)
        shots = [(100.0, 100.0)] * 6
        score = score_image(targets, protected, centers, shots, radius)
        self.assertEqual(score["misses"], 6)
        self.assertEqual(score["miss_penalty"], 2)
    
    def test_all_enemy_eliminated_bonus(self):
        """Test the bonus for eliminating all enemy targets."""
        targets = {1, 2}  # Two target species
        protected = set()
        centers = [((15.0, 15.0), 1), ((25.0, 25.0), 2)]
        radius = 5.0
        
        # Hit all targets - should get bonus
        shots = [(15.0, 15.0), (25.0, 25.0)]
        score = score_image(targets, protected, centers, shots, radius)
        self.assertEqual(score["correct"], 2)
        self.assertEqual(score["bonus_all_enemy_down"], 1)
        
        # Miss one target - should not get bonus
        shots = [(15.0, 15.0), (100.0, 100.0)]  # Second shot misses
        score = score_image(targets, protected, centers, shots, radius)
        self.assertEqual(score["correct"], 1)
        self.assertEqual(score["bonus_all_enemy_down"], 0)
        
        # No targets present - should not get bonus
        centers = [((15.0, 15.0), 3)]  # Only non-target species
        shots = [(15.0, 15.0)]
        score = score_image(targets, protected, centers, shots, radius)
        self.assertEqual(score["correct"], 0)
        self.assertEqual(score["bonus_all_enemy_down"], 0)
    
    def test_collateral_damage_penalty(self):
        """Test penalty for hitting protected species."""
        targets = set()
        protected = {1, 2}  # Both species are protected
        centers = [((15.0, 15.0), 1), ((25.0, 25.0), 2)]
        radius = 5.0
        
        # Hit both protected species
        shots = [(15.0, 15.0), (25.0, 25.0)]
        score = score_image(targets, protected, centers, shots, radius)
        
        self.assertEqual(score["correct"], 0)
        self.assertEqual(score["collateral"], 2)
        self.assertEqual(score["misses"], 0)
        self.assertEqual(score["bonus_all_enemy_down"], 0)
        
        # Total score: +0 (correct) +0 (bonus) -2 (collateral) -0 (miss penalty) = -2
        self.assertEqual(score["total"], -2)
    
    def test_neutral_hits_no_penalty(self):
        """Test that hits on neutral species don't get penalty or reward."""
        targets = set()
        protected = set()
        centers = [((15.0, 15.0), 3), ((25.0, 25.0), 4)]  # Neutral species
        radius = 5.0
        
        shots = [(15.0, 15.0), (25.0, 25.0)]
        score = score_image(targets, protected, centers, shots, radius)
        
        self.assertEqual(score["correct"], 0)
        self.assertEqual(score["collateral"], 0)
        self.assertEqual(score["misses"], 0)
        self.assertEqual(score["total"], 0)  # No penalty, no reward
    
    def test_radius_sensitivity_analysis(self):
        """Test comprehensive radius sensitivity analysis."""
        targets = {1, 2}
        protected = {3}
        centers = [((10.0, 10.0), 1), ((20.0, 20.0), 2), ((30.0, 30.0), 3)]
        shots = [(12.0, 12.0), (22.0, 22.0), (32.0, 32.0)]  # Close to centers
        
        radii = [1.0, 3.0, 5.0, 8.0, 10.0, 15.0, 20.0]
        results = []
        
        for radius in radii:
            score = score_image(targets, protected, centers, shots, radius)
            results.append({
                "radius": radius,
                "total": score["total"],
                "correct": score["correct"],
                "collateral": score["collateral"],
                "misses": score["misses"]
            })
        
        # Verify that performance generally improves with larger radius
        # (more shots hit targets, fewer misses)
        for i in range(1, len(results)):
            if results[i-1]["misses"] > 0 and results[i]["misses"] == 0:
                # If we go from having misses to no misses, score should improve
                self.assertGreaterEqual(results[i]["total"], results[i-1]["total"])


if __name__ == "__main__":
    unittest.main()

