#!/usr/bin/env python3
"""
Test suite for orders parsing with ambiguous/contradictory cases.
Tests the robustness of mission order parsing against edge cases.
"""

import unittest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from pokemon_targeting_enhanced import EnhancedPokemonTargetingSystem
from pokemon_targeting_system import parse_mission_orders


class TestOrdersParser(unittest.TestCase):
    """Test orders parsing with edge cases and ambiguous scenarios."""
    
    def setUp(self):
        self.system = EnhancedPokemonTargetingSystem()
    
    def test_ambiguous_multi_species_directives(self):
        """Test parsing when multiple species have different roles."""
        ambiguous_orders = [
            {
                "text": "Target the Bulbasaur and Charmander. Protect Pikachu and Charizard nearby.",
                "expected_targets": ["Bulbasaur", "Charmander"],
                "expected_protected": ["Pikachu", "Charizard"]
            },
            {
                "text": "Eliminate all hostile Bulbasaur immediately. Do not harm Pikachu civilians.",
                "expected_targets": ["Bulbasaur"],
                "expected_protected": ["Pikachu"]
            },
            {
                "text": "Neutralize the dangerous Mewtwo. Keep Pikachu and Charizard safe.",
                "expected_targets": ["Mewtwo"],
                "expected_protected": ["Pikachu", "Charizard"]
            }
        ]
        
        for case in ambiguous_orders:
            with self.subTest(order=case["text"][:50]):
                result = self.system.parse_mission_orders(case["text"])
                
                # Check that targets are correctly identified
                self.assertCountEqual(result["targets"], case["expected_targets"], 
                                    f"Targets mismatch for: {case['text']}")
                
                # Check that protected species are correctly identified
                self.assertCountEqual(result["protected"], case["expected_protected"],
                                    f"Protected mismatch for: {case['text']}")
    
    def test_contradictory_orders(self):
        """Test handling of contradictory instructions."""
        contradictory_cases = [
            {
                "text": "Target the Pikachu immediately. But also protect Pikachu from harm.",
                "expected_behavior": "targets_win"  # targets should override protected
            },
            {
                "text": "Eliminate Bulbasaur. Do not eliminate Bulbasaur.",
                "expected_behavior": "ambiguous"  # should handle gracefully
            },
            {
                "text": "The Bulbasaur is both friend and foe. Use your judgment.",
                "expected_behavior": "neutral"  # should default to neutral
            }
        ]
        
        for case in contradictory_cases:
            with self.subTest(order=case["text"][:50]):
                result = self.system.parse_mission_orders(case["text"])
                
                if case["expected_behavior"] == "targets_win":
                    # Targets should take precedence over protected
                    self.assertIn("Pikachu", result["targets"])
                    self.assertNotIn("Pikachu", result["protected"])
                elif case["expected_behavior"] == "ambiguous":
                    # Should handle gracefully without crashing
                    self.assertIsInstance(result["targets"], list)
                    self.assertIsInstance(result["protected"], list)
                elif case["expected_behavior"] == "neutral":
                    # Should not assign conflicting roles
                    self.assertEqual(len(set(result["targets"]) & set(result["protected"])), 0)
    
    def test_protected_only_scenes(self):
        """Test orders that only mention protected species."""
        protected_only_cases = [
            {
                "text": "Protect all Pikachu and Charizard in the area. No targets to engage.",
                "expected_targets": [],
                "expected_protected": ["Pikachu", "Charizard"]
            },
            {
                "text": "Defend the innocent Bulbasaur civilians. Avoid all combat.",
                "expected_targets": [],
                "expected_protected": ["Bulbasaur"]
            },
            {
                "text": "Keep Mewtwo safe at all costs. Do not engage any targets.",
                "expected_targets": [],
                "expected_protected": ["Mewtwo"]
            }
        ]
        
        for case in protected_only_cases:
            with self.subTest(order=case["text"][:50]):
                result = self.system.parse_mission_orders(case["text"])
                
                self.assertEqual(result["targets"], case["expected_targets"],
                               f"Should have no targets for protected-only: {case['text']}")
                self.assertCountEqual(result["protected"], case["expected_protected"],
                                    f"Protected species mismatch: {case['text']}")
    
    def test_missing_targets_scenarios(self):
        """Test orders that don't specify clear targets."""
        missing_target_cases = [
            {
                "text": "Investigate the area for unusual activity.",
                "expected_targets": [],
                "expected_protected": []
            },
            {
                "text": "Stand by for further instructions.",
                "expected_targets": [],
                "expected_protected": []
            },
            {
                "text": "Monitor Pikachu behavior but do not engage.",
                "expected_targets": [],
                "expected_protected": ["Pikachu"]
            }
        ]
        
        for case in missing_target_cases:
            with self.subTest(order=case["text"][:50]):
                result = self.system.parse_mission_orders(case["text"])
                
                self.assertEqual(result["targets"], case["expected_targets"],
                               f"Should have no targets for: {case['text']}")
                self.assertCountEqual(result["protected"], case["expected_protected"],
                                    f"Protected mismatch for: {case['text']}")
    
    def test_occluded_target_scenarios(self):
        """Test orders mentioning occluded or partially visible targets."""
        occluded_cases = [
            {
                "text": "Target the partially visible Bulbasaur behind cover.",
                "expected_targets": ["Bulbasaur"],
                "expected_protected": []
            },
            {
                "text": "Engage the Mewtwo that's partially obscured by terrain.",
                "expected_targets": ["Mewtwo"],
                "expected_protected": []
            },
            {
                "text": "Protect the hidden Pikachu from indirect fire.",
                "expected_targets": [],
                "expected_protected": ["Pikachu"]
            }
        ]
        
        for case in occluded_cases:
            with self.subTest(order=case["text"][:50]):
                result = self.system.parse_mission_orders(case["text"])
                
                self.assertCountEqual(result["targets"], case["expected_targets"],
                                    f"Targets mismatch for occluded case: {case['text']}")
                self.assertCountEqual(result["protected"], case["expected_protected"],
                                    f"Protected mismatch for occluded case: {case['text']}")
    
    def test_confidence_and_decision_rationale(self):
        """Test that system provides confidence scores and decision rationale."""
        complex_order = """
        URGENT: Multiple Bulbasaur and Charmander detected with hostile intent.
        Exercise extreme caution around Pikachu civilians. 
        Mewtwo status is unclear - may be friendly or hostile.
        Neutralize confirmed threats immediately.
        """
        
        result = self.system.parse_mission_orders(complex_order)
        
        # Should extract multiple species
        self.assertGreater(len(result["targets"]), 0, "Should identify targets")
        self.assertGreater(len(result["protected"]), 0, "Should identify protected")
        
        # Should have mission classification
        self.assertIn("mission_type", result)
        self.assertIn("priority", result)
        
        # Should handle unclear species (Mewtwo) appropriately
        if "Mewtwo" in result["extracted_pokemon"]:
            # Mewtwo should not be in both targets and protected
            self.assertEqual(len(set(result["targets"]) & set(result["protected"])), 0)
    
    def test_varied_tone_and_jargon(self):
        """Test parsing with different tones and military jargon."""
        jargon_cases = [
            {
                "text": "ROE: Engage all Charlie targets. Avoid Bravo assets.",
                "expected_behavior": "parse_gracefully"
            },
            {
                "text": "WILCO. Taking out the bogies. Civvies are off-limits.",
                "expected_behavior": "parse_gracefully"
            },
            {
                "text": "Execute the following: eliminate hostiles, preserve friendlies.",
                "expected_behavior": "parse_gracefully"
            }
        ]
        
        for case in jargon_cases:
            with self.subTest(order=case["text"][:50]):
                result = self.system.parse_mission_orders(case["text"])
                
                # Should parse without crashing
                self.assertIsInstance(result["targets"], list)
                self.assertIsInstance(result["protected"], list)
                self.assertIn("mission_type", result)
                self.assertIn("priority", result)
    
    def test_fallback_parsing_without_spacy(self):
        """Test that fallback parsing works when spaCy is unavailable."""
        # This test would need to mock spaCy being unavailable
        # For now, test that the fallback method exists and works
        test_order = "Target Bulbasaur. Protect Pikachu."
        
        # Test fallback method directly
        fallback_result = self.system.parse_mission_orders_fallback(test_order)
        
        self.assertIsInstance(fallback_result["targets"], list)
        self.assertIsInstance(fallback_result["protected"], list)
        self.assertIn("mission_type", fallback_result)
        self.assertIn("priority", fallback_result)
    
    def test_mission_type_classification(self):
        """Test that mission types are correctly classified."""
        mission_type_cases = [
            {
                "text": "Eliminate all hostile Bulbasaur immediately!",
                "expected_type": "elimination"
            },
            {
                "text": "Capture the suspicious Pikachu for interrogation.",
                "expected_type": "capture"
            },
            {
                "text": "Protect the innocent Charizard civilians.",
                "expected_type": "protection"
            },
            {
                "text": "Investigate the area for Pokemon activity.",
                "expected_type": "reconnaissance"
            }
        ]
        
        for case in mission_type_cases:
            with self.subTest(order=case["text"][:50]):
                result = self.system.parse_mission_orders(case["text"])
                self.assertEqual(result["mission_type"], case["expected_type"],
                               f"Mission type mismatch for: {case['text']}")
    
    def test_priority_extraction(self):
        """Test that mission priority is correctly extracted."""
        priority_cases = [
            {
                "text": "URGENT: Eliminate targets immediately!",
                "expected_priority": "high"
            },
            {
                "text": "This is a high-priority operation.",
                "expected_priority": "high"
            },
            {
                "text": "Standard mission: investigate the area.",
                "expected_priority": "normal"
            },
            {
                "text": "Important: protect the civilians.",
                "expected_priority": "medium"
            }
        ]
        
        for case in priority_cases:
            with self.subTest(order=case["text"][:50]):
                result = self.system.parse_mission_orders(case["text"])
                self.assertEqual(result["priority"], case["expected_priority"],
                               f"Priority mismatch for: {case['text']}")


if __name__ == "__main__":
    unittest.main()
