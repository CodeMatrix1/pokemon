#!/usr/bin/env python3
"""
Test script for the Pokémon Targeting System
"""

import pandas as pd
import json

from pokemon_targeting_system import (
    parse_mission_orders, 
    detect_pokemon_in_image, 
    generate_targeting_coordinates,
    extract_pokemon_names,
    is_target_species,
    is_protected_species
)

def test_nlp_parsing():
    """Test the NLP parsing functionality"""
    print("=== Testing NLP Parsing ===")
    
    test_orders = [
        "HQ has detected unusual Bulbasaur activity. Neutralize them immediately. Protect Pikachu nearby.",
        "Eliminate all Charizard in the area. Remember to avoid hitting Squirtle civilians.",
        "Target the suspicious Pidgey. Don't draw the friendly Eevee into combat.",
        "Destroy the hostile Mewtwo. Take care not to harm the innocent Clefairy."
    ]
    
    for i, order in enumerate(test_orders, 1):
        print(f"\nTest {i}: {order}")
        result = parse_mission_orders(order)
        print(f"  Targets: {result['targets']}")
        print(f"  Protected: {result['protected']}")

def test_pokemon_extraction():
    """Test Pokémon name extraction"""
    print("\n=== Testing Pokémon Name Extraction ===")
    
    test_text = "I see Bulbasaur, Pikachu, and Charizard in the area. Also spotted a Mewtwo nearby."
    pokemon = extract_pokemon_names(test_text)
    print(f"Text: {test_text}")
    print(f"Extracted Pokémon: {pokemon}")

def test_context_analysis():
    """Test context analysis for target/protected classification"""
    print("\n=== Testing Context Analysis ===")
    
    test_cases = [
        ("neutralize the Bulbasaur immediately", "Bulbasaur", "target"),
        ("protect the Pikachu nearby", "Pikachu", "protected"),
        ("eliminate all Charizard", "Charizard", "target"),
        ("don't harm the Squirtle", "Squirtle", "protected"),
        ("destroy the hostile Mewtwo", "Mewtwo", "target"),
        ("take care not to hit Eevee", "Eevee", "protected")
    ]
    
    for context, pokemon, expected in test_cases:
        is_target = is_target_species(context)
        is_protected = is_protected_species(context)
        
        result = "target" if is_target else ("protected" if is_protected else "neutral")
        status = "✓" if result == expected else "✗"
        
        print(f"{status} {pokemon}: {context} -> {result} (expected: {expected})")

def test_full_system(image_path, mission_orders):
    """Test the complete targeting system"""
    print("\n=== Testing Full System ===")
    
    print("Mission Orders:")
    print(mission_orders.strip())
    print()
    
    coordinates = generate_targeting_coordinates(image_path, mission_orders)
    print(f"\nFinal targeting coordinates: {coordinates}")
    return coordinates

def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n=== Testing Edge Cases ===")
    
    # Test with empty mission orders
    print("1. Empty mission orders:")
    result = parse_mission_orders("")
    print(f"   Result: {result}")
    
    # Test with no Pokémon mentioned
    print("\n2. No Pokémon mentioned:")
    result = parse_mission_orders("The weather is nice today.")
    print(f"   Result: {result}")
    
    # Test with conflicting instructions
    print("\n3. Conflicting instructions:")
    result = parse_mission_orders("Neutralize Pikachu but also protect Pikachu.")
    print(f"   Result: {result}")
    
    # Test with non-existent image
    print("\n4. Non-existent image file:")
    coordinates = generate_targeting_coordinates("nonexistent.png", "Target Bulbasaur.")
    print(f"   Coordinates: {coordinates}")

def main():
    """Run all tests"""
    results=[]
    with open("kaggle_fold/test_prompts_orders.json", "r") as f:
        data = json.load(f)
    prompts=data
    i=1
    for prompt in prompts:
        print(f"Pokémon Test No-{i}")
        print("=" * 50)
        ans=[]
        if prompt:
            try:
                coords=test_full_system("kaggle_fold/"+"test_images/"+prompt["image_id"], prompt["prompt"])
                print("Final Coordinates:", coords)
                ans.extend(coords)
                
            except Exception as e:
                print(f"\nTest failed with error: {e} and prompt: {i}.{prompt}")
                import traceback
                traceback.print_exc()
        results.append({"image_id":prompt["image_id"],"points":ans})
        print("\n" + "=" * 50)
        i+=1
    print("All tests completed!")
    df = pd.DataFrame(results)
    df.to_csv("mission_results.csv", index=False)
    print("Results saved to mission_results.csv")


if __name__ == "__main__":
    main()

