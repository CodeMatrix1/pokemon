#!/usr/bin/env python3
"""
Comprehensive Demo of the Enhanced Pokémon Targeting System
This script demonstrates all the features and capabilities of the system.
"""

from pokemon_targeting_enhanced import EnhancedPokemonTargetingSystem
import json
import os

def demo_basic_functionality():
    """
    Demonstrate basic system functionality.
    """
    print("=" * 60)
    print("DEMO 1: Basic Functionality")
    print("=" * 60)
    
    system = EnhancedPokemonTargetingSystem()
    
    # Simple mission
    mission = "Target the Bulbasaur. Protect Pikachu nearby."
    result = system.generate_targeting_coordinates("dummy.png", mission)
    
    print(f"Mission: {mission}")
    print(f"Targets: {result['mission_analysis']['targets']}")
    print(f"Protected: {result['mission_analysis']['protected']}")
    print(f"Coordinates: {result['coordinates']}")
    print()

def demo_mission_types():
    """
    Demonstrate different mission types and priorities.
    """
    print("=" * 60)
    print("DEMO 2: Mission Types and Priorities")
    print("=" * 60)
    
    system = EnhancedPokemonTargetingSystem()
    
    missions = [
        {
            "name": "Elimination Mission",
            "text": "URGENT: Eliminate all hostile Charizard in the area immediately!"
        },
        {
            "name": "Capture Mission", 
            "text": "Capture the suspicious Pikachu for investigation. Avoid harming Squirtle civilians."
        },
        {
            "name": "Protection Mission",
            "text": "Protect the innocent Eevee from the dangerous Mewtwo. Defend at all costs."
        },
        {
            "name": "Reconnaissance Mission",
            "text": "Investigate the area for any unusual Pokémon activity. Report findings."
        }
    ]
    
    for mission in missions:
        print(f"\n{mission['name']}:")
        print(f"Text: {mission['text']}")
        
        result = system.generate_targeting_coordinates("dummy.png", mission['text'])
        analysis = result['mission_analysis']
        
        print(f"  Type: {analysis['mission_type']}")
        print(f"  Priority: {analysis['priority']}")
        print(f"  Targets: {analysis['targets']}")
        print(f"  Protected: {analysis['protected']}")
        print(f"  Coordinates: {result['coordinates']}")

def demo_complex_scenarios():
    """
    Demonstrate complex mission scenarios.
    """
    print("=" * 60)
    print("DEMO 3: Complex Mission Scenarios")
    print("=" * 60)
    
    system = EnhancedPokemonTargetingSystem()
    
    complex_missions = [
        {
            "name": "Multi-Species Elimination",
            "text": """
            CRITICAL MISSION: Multiple hostile Pokémon detected in Sector Alpha.
            Eliminate all Bulbasaur, Charmander, and Squirtle immediately.
            Avoid collateral damage to Pikachu and Eevee civilians.
            This is a high-priority operation with zero tolerance for failure.
            """
        },
        {
            "name": "Ambiguous Instructions",
            "text": """
            HQ reports unusual activity involving Pikachu and Charizard.
            The Pikachu may be hostile, but the Charizard are definitely friendly.
            Use your judgment to determine appropriate action.
            """
        },
        {
            "name": "Conflicting Orders",
            "text": """
            URGENT: Neutralize the Mewtwo immediately!
            But also protect the Mewtwo from harm.
            This is a classified operation with conflicting objectives.
            """
        }
    ]
    
    for mission in complex_missions:
        print(f"\n{mission['name']}:")
        print(f"Text: {mission['text'].strip()}")
        
        result = system.generate_targeting_coordinates("dummy.png", mission['text'])
        analysis = result['mission_analysis']
        
        print(f"  Analysis:")
        print(f"    Type: {analysis['mission_type']}")
        print(f"    Priority: {analysis['priority']}")
        print(f"    All Pokémon: {analysis['extracted_pokemon']}")
        print(f"    Targets: {analysis['targets']}")
        print(f"    Protected: {analysis['protected']}")
        
        print(f"  Targeting Details:")
        for detail in result['details']:
            status_icon = "✓" if detail['status'] == 'target' else "⚠" if detail['status'] == 'protected' else "-"
            coords = f" at {detail['coordinates']}" if detail['coordinates'] else ""
            print(f"    {status_icon} {detail['species']}: {detail['status']} (conf: {detail['confidence']:.2f}){coords}")

def demo_error_handling():
    """
    Demonstrate error handling and edge cases.
    """
    print("=" * 60)
    print("DEMO 4: Error Handling and Edge Cases")
    print("=" * 60)
    
    system = EnhancedPokemonTargetingSystem()
    
    edge_cases = [
        {
            "name": "Empty Mission",
            "text": ""
        },
        {
            "name": "No Pokémon Mentioned",
            "text": "The weather is nice today. Nothing to report."
        },
        {
            "name": "Invalid Pokémon Names",
            "text": "Target the Pikachuu and Charizardd. Avoid the Bulbasaurr."
        },
        {
            "name": "Very Long Mission",
            "text": "This is a very long mission description that goes on and on and on and mentions many different things and has lots of text but no actual Pokémon names in it so it should be handled gracefully by the system without crashing or producing errors."
        }
    ]
    
    for case in edge_cases:
        print(f"\n{case['name']}:")
        print(f"Text: '{case['text']}'")
        
        try:
            result = system.generate_targeting_coordinates("nonexistent.png", case['text'])
            analysis = result['mission_analysis']
            
            print(f"  Result: SUCCESS")
            print(f"    Type: {analysis['mission_type']}")
            print(f"    Priority: {analysis['priority']}")
            print(f"    Targets: {analysis['targets']}")
            print(f"    Protected: {analysis['protected']}")
            print(f"    Coordinates: {result['coordinates']}")
            
        except Exception as e:
            print(f"  Result: ERROR - {e}")

def demo_mission_history():
    """
    Demonstrate mission history tracking.
    """
    print("=" * 60)
    print("DEMO 5: Mission History Tracking")
    print("=" * 60)
    
    system = EnhancedPokemonTargetingSystem()
    
    # Process multiple missions
    missions = [
        "Target Bulbasaur. Protect Pikachu.",
        "Eliminate Charizard immediately!",
        "Capture the suspicious Eevee."
    ]
    
    for i, mission in enumerate(missions, 1):
        print(f"\nProcessing Mission {i}: {mission}")
        result = system.generate_targeting_coordinates("dummy.png", mission)
        print(f"  Coordinates: {result['coordinates']}")
    
    # Show mission history
    history = system.get_mission_history()
    print(f"\nMission History ({len(history)} missions):")
    
    for i, mission in enumerate(history, 1):
        print(f"  Mission {i}:")
        print(f"    Time: {mission['timestamp']}")
        print(f"    Type: {mission['orders']['mission_type']}")
        print(f"    Priority: {mission['orders']['priority']}")
        print(f"    Targets: {mission['orders']['targets']}")
        print(f"    Coordinates: {[d['coordinates'] for d in mission['targeting'] if d['coordinates']]}")

def demo_report_generation():
    """
    Demonstrate report generation capabilities.
    """
    print("=" * 60)
    print("DEMO 6: Report Generation")
    print("=" * 60)
    
    system = EnhancedPokemonTargetingSystem()
    
    # Complex mission for detailed report
    mission = """
    URGENT ELIMINATION MISSION: Sector 7 has been compromised by hostile Pokémon activity.
    Multiple Bulbasaur and Charmander have been detected exhibiting aggressive behavior.
    Immediate neutralization is required to prevent civilian casualties.
    Exercise extreme caution around Pikachu and Eevee - they are friendly and must be protected.
    This is a high-priority operation with authorization for lethal force.
    """
    
    print("Processing complex mission for detailed report...")
    result = system.generate_targeting_coordinates("dummy.png", mission)
    
    # Save detailed report
    system.save_mission_report(result, "demo_mission_report.json")
    
    # Show report summary
    print("\nReport Summary:")
    print(f"  Mission Type: {result['mission_analysis']['mission_type']}")
    print(f"  Priority: {result['mission_analysis']['priority']}")
    print(f"  Target Species: {result['mission_analysis']['targets']}")
    print(f"  Protected Species: {result['mission_analysis']['protected']}")
    print(f"  Targeting Coordinates: {result['coordinates']}")
    print(f"  Total Detections: {len(result['detection_results'])}")
    
    # Show targeting details
    print(f"\nTargeting Details:")
    for detail in result['details']:
        if detail['coordinates']:
            print(f"  ✓ {detail['species']}: Target at {detail['coordinates']} (conf: {detail['confidence']:.2f})")
        else:
            print(f"  - {detail['species']}: {detail['status']} (conf: {detail['confidence']:.2f})")

def main():
    """
    Run all demonstration scenarios.
    """
    print("ENHANCED POKÉMON TARGETING SYSTEM - COMPREHENSIVE DEMO")
    print("=" * 80)
    print()
    
    try:
        demo_basic_functionality()
        demo_mission_types()
        demo_complex_scenarios()
        demo_error_handling()
        demo_mission_history()
        demo_report_generation()
        
        print("\n" + "=" * 80)
        print("ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print()
        print("Generated files:")
        print("  - demo_mission_report.json (detailed mission report)")
        print("  - enhanced_mission_report.json (from main system)")
        print("  - mission_report.json (from basic system)")
        print()
        print("The system is ready for production use!")
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()


