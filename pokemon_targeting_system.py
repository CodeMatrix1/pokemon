# Import necessary libraries
import cv2  # OpenCV for computer vision tasks
import json  # For parsing JSON files
import spacy  # For NLP tasks like Named Entity Recognition
import numpy as np  # For handling image arrays
from typing import List, Tuple, Dict
import os
import re

# Initialize NLP model (you can use pre-trained models like spaCy for NER)
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Warning: spaCy model 'en_core_web_sm' not found. Please install it with: python -m spacy download en_core_web_sm")
    nlp = None

# 1. Function to parse HQ mission orders (NLP)
def parse_mission_orders(order_text: str) -> dict:
    """
    Parses the HQ orders and extracts critical information about target species and protected species.
    
    :param order_text: Raw text from HQ orders
    :return: Dictionary with extracted information
    """
    if nlp is None:
        # Fallback parsing without spaCy
        return parse_mission_orders_fallback(order_text)
    
    doc = nlp(order_text)
    targets = []
    protected = []
    
    # Enhanced NER to extract Pokémon names and roles
    # Look for common patterns in mission orders
    pokemon_names = extract_pokemon_names(order_text)
    
    # Use context clues to determine if a Pokémon is a target or protected
    for pokemon in pokemon_names:
        context = get_pokemon_context(order_text, pokemon)
        if is_target_species(context):
            targets.append(pokemon)
        elif is_protected_species(context):
            protected.append(pokemon)
    
    return {
        "targets": targets,
        "protected": protected,
        "raw_text": order_text
    }

def parse_mission_orders_fallback(order_text: str) -> dict:
    """
    Fallback parsing method when spaCy is not available.
    Uses regex patterns to extract Pokémon names and context.
    """
    pokemon_names = extract_pokemon_names(order_text)
    targets = []
    protected = []
    
    for pokemon in pokemon_names:
        context = get_pokemon_context(order_text, pokemon)
        if is_target_species(context):
            targets.append(pokemon)
        elif is_protected_species(context):
            protected.append(pokemon)
    
    return {
        "targets": targets,
        "protected": protected,
        "raw_text": order_text
    }

def extract_pokemon_names(text: str) -> List[str]:
    """
    Extract Pokémon names from text using common patterns.
    """
    # Common Pokémon names (you can expand this list)
    pokemon_list = [
        "Bulbasaur", "Ivysaur", "Venusaur", "Charmander", "Charmeleon", "Charizard",
        "Squirtle", "Wartortle", "Blastoise", "Caterpie", "Metapod", "Butterfree",
        "Weedle", "Kakuna", "Beedrill", "Pidgey", "Pidgeotto", "Pidgeot",
        "Rattata", "Raticate", "Spearow", "Fearow", "Ekans", "Arbok",
        "Pikachu", "Raichu", "Sandshrew", "Sandslash", "Nidoran", "Nidorina",
        "Nidorino", "Nidoqueen", "Nidoking", "Clefairy", "Clefable", "Vulpix",
        "Ninetales", "Jigglypuff", "Wigglytuff", "Zubat", "Golbat", "Oddish",
        "Gloom", "Vileplume", "Paras", "Parasect", "Venonat", "Venomoth",
        "Diglett", "Dugtrio", "Meowth", "Persian", "Psyduck", "Golduck",
        "Mankey", "Primeape", "Growlithe", "Arcanine", "Poliwag", "Poliwhirl",
        "Poliwrath", "Abra", "Kadabra", "Alakazam", "Machop", "Machoke",
        "Machamp", "Bellsprout", "Weepinbell", "Victreebel", "Tentacool",
        "Tentacruel", "Geodude", "Graveler", "Golem", "Ponyta", "Rapidash",
        "Slowpoke", "Slowbro", "Magnemite", "Magneton", "Farfetch'd",
        "Doduo", "Dodrio", "Seel", "Dewgong", "Grimer", "Muk", "Shellder",
        "Cloyster", "Gastly", "Haunter", "Gengar", "Onix", "Drowzee",
        "Hypno", "Krabby", "Kingler", "Voltorb", "Electrode", "Exeggcute",
        "Exeggutor", "Cubone", "Marowak", "Hitmonlee", "Hitmonchan",
        "Lickitung", "Koffing", "Weezing", "Rhyhorn", "Rhydon", "Chansey",
        "Tangela", "Kangaskhan", "Horsea", "Seadra", "Goldeen", "Seaking",
        "Staryu", "Starmie", "Mr. Mime", "Scyther", "Jynx", "Electabuzz",
        "Magmar", "Pinsir", "Tauros", "Magikarp", "Gyarados", "Lapras",
        "Ditto", "Eevee", "Vaporeon", "Jolteon", "Flareon", "Porygon",
        "Omanyte", "Omastar", "Kabuto", "Kabutops", "Aerodactyl", "Snorlax",
        "Articuno", "Zapdos", "Moltres", "Dratini", "Dragonair", "Dragonite",
        "Mewtwo", "Mew"
    ]
    
    found_pokemon = []
    text_lower = text.lower()
    
    for pokemon in pokemon_list:
        if pokemon.lower() in text_lower:
            found_pokemon.append(pokemon)
    
    return found_pokemon

def get_pokemon_context(text: str, pokemon: str) -> str:
    """
    Get the context around a Pokémon name in the text.
    """
    # Find the position of the Pokémon name
    pokemon_lower = pokemon.lower()
    text_lower = text.lower()
    
    start_pos = text_lower.find(pokemon_lower)
    if start_pos == -1:
        return ""
    
    # Extract context (50 characters before and after)
    context_start = max(0, start_pos - 50)
    context_end = min(len(text), start_pos + len(pokemon) + 50)
    
    return text[context_start:context_end]

def is_target_species(context: str) -> bool:
    """
    Determine if a Pokémon is a target species based on context.
    """
    target_keywords = [
        "neutralize", "eliminate", "destroy", "target", "threat", "dangerous",
        "hostile", "attack", "combat", "defeat", "stop", "prevent", "anomalous",
        "unusual", "suspicious", "imminent threat", "must be stopped"
    ]
    
    context_lower = context.lower()
    return any(keyword in context_lower for keyword in target_keywords)

def is_protected_species(context: str) -> bool:
    """
    Determine if a Pokémon is a protected species based on context.
    """
    protected_keywords = [
        "protect", "care", "don't", "avoid", "spare", "safe", "friendly",
        "ally", "innocent", "civilians", "draw into combat", "not to",
        "remember", "nearby", "take care"
    ]
    
    context_lower = context.lower()
    return any(keyword in context_lower for keyword in protected_keywords)

# 2. Function to process battlefield images (CV)
def detect_pokemon_in_image(image_path: str) -> List[dict]:
    """
    Detects Pokémon in a battlefield image and returns bounding boxes with species labels.
    
    :param image_path: Path to the battlefield image
    :return: List of detected Pokémon with bounding boxes and species labels
    """
    if not os.path.exists(image_path):
        print(f"Warning: Image file {image_path} not found. Using dummy data.")
        return get_dummy_detections()
    
    image = cv2.imread(image_path)
    if image is None:
        print(f"Warning: Could not load image {image_path}. Using dummy data.")
        return get_dummy_detections()
    
    pokemon_detections = []
    
    # Placeholder: use a pre-trained object detection model (e.g., YOLO or Faster R-CNN)
    # Here we simulate detection with dummy data for now
    # In a real implementation, you would integrate YOLO or another detection model here
    pokemon_detections = get_dummy_detections()
    
    return pokemon_detections

def get_dummy_detections() -> List[dict]:
    """
    Returns dummy detection data for testing purposes.
    """
    return [
        {
            "species": "Bulbasaur",
            "bounding_box": [100, 150, 50, 50],  # [x, y, width, height]
            "confidence": 0.95
        },
        {
            "species": "Pikachu",
            "bounding_box": [200, 250, 50, 50],
            "confidence": 0.87
        },
        {
            "species": "Charizard",
            "bounding_box": [300, 100, 80, 80],
            "confidence": 0.92
        }
    ]

# 3. Function to generate targeting coordinates (Integrate NLP and CV)
def generate_targeting_coordinates(image_path: str, mission_orders: str) -> List[Tuple[float, float]]:
    """
    Generates targeting coordinates based on mission orders and battlefield image detections.
    
    :param image_path: Path to the battlefield image
    :param mission_orders: HQ mission orders
    :return: List of targeting coordinates
    """
    # Step 1: Parse mission orders
    parsed_orders = parse_mission_orders(mission_orders)
    targets = parsed_orders["targets"]
    protected = parsed_orders["protected"]
    
    print(f"Mission Analysis:")
    print(f"  Target species: {targets}")
    print(f"  Protected species: {protected}")
    
    # Step 2: Detect Pokémon in the image
    detected_pokemon = detect_pokemon_in_image(image_path)
    
    print(f"Detected Pokémon: {[p['species'] for p in detected_pokemon]}")
    
    # Step 3: Filter Pokémon based on mission orders (target species only)
    targeting_coordinates = []
    
    for pokemon in detected_pokemon:
        species = pokemon["species"]
        if species in targets:
            # Calculate the center of the bounding box as the targeting coordinates
            x, y, w, h = pokemon["bounding_box"]
            target_coord = (x + w / 2, y + h / 2)
            targeting_coordinates.append(target_coord)
            print(f"  Targeting {species} at coordinates: {target_coord}")
        elif species in protected:
            print(f"  Skipping protected species: {species}")
        else:
            print(f"  Species {species} not mentioned in mission orders")
    
    return targeting_coordinates

def save_mission_report(coordinates: List[Tuple[float, float]], 
                       parsed_orders: dict, 
                       detected_pokemon: List[dict],
                       output_file: str = "mission_report.json"):
    """
    Save a detailed mission report to a JSON file.
    """
    report = {
        "mission_summary": {
            "targets": parsed_orders["targets"],
            "protected": parsed_orders["protected"],
            "targeting_coordinates": coordinates
        },
        "detection_results": detected_pokemon,
        "raw_orders": parsed_orders["raw_text"]
    }
    
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Mission report saved to {output_file}")

# Example usage and testing
def main():
    """
    Main function to demonstrate the Pokémon targeting system.
    """
    print("=== Pokémon Targeting System ===")
    print()
    
    # Example mission orders
    mission_orders = """
    HQ has detected unusual Bulbasaur activity in the area. Field sensors logged anomalous behavior that suggests an imminent threat.
    Remember there are Pikachu and Charizard nearby — take care not to draw them into combat. 
    You are to neutralize the bulbasaurs immediately.
    """
    
    # Example image path (you can replace this with actual image paths)
    image_path = "battlefield_image.png"
    
    print("Processing mission orders...")
    coordinates = generate_targeting_coordinates(image_path, mission_orders)
    
    print(f"\nFinal targeting coordinates: {coordinates}")
    
    # Save mission report
    parsed_orders = parse_mission_orders(mission_orders)
    detected_pokemon = detect_pokemon_in_image(image_path)
    save_mission_report(coordinates, parsed_orders, detected_pokemon)
    
    print("\nMission analysis complete!")

if __name__ == "__main__":
    main()

