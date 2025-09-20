#!/usr/bin/env python3
"""
Enhanced Pokémon Targeting System
Combines advanced NLP parsing with improved computer vision detection.
"""

import cv2
import json
import spacy
import numpy as np
from typing import List, Tuple, Dict, Optional
import os
import re
from enhanced_detection import PokemonDetector

# Initialize NLP model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Warning: spaCy model 'en_core_web_sm' not found. Please install it with: python -m spacy download en_core_web_sm")
    nlp = None

class EnhancedPokemonTargetingSystem:
    """
    Enhanced Pokémon targeting system with improved NLP and CV capabilities.
    """
    
    def __init__(self, detection_model_path: Optional[str] = None):
        """
        Initialize the enhanced targeting system.
        
        :param detection_model_path: Path to detection model files
        """
        self.detector = PokemonDetector(detection_model_path)
        self.mission_history = []
    
    def parse_mission_orders(self, order_text: str) -> Dict:
        """
        Enhanced mission order parsing with better context analysis.
        """
        if nlp is None:
            return self.parse_mission_orders_fallback(order_text)
        
        doc = nlp(order_text)
        targets = []
        protected = []
        mission_type = "unknown"
        priority = "normal"
        
        # Extract mission type and priority
        mission_type = self.extract_mission_type(order_text)
        priority = self.extract_priority(order_text)
        
        # Extract Pokémon names and their roles
        pokemon_names = self.extract_pokemon_names(order_text)
        
        for pokemon in pokemon_names:
            context = self.get_pokemon_context(order_text, pokemon)
            role = self.classify_pokemon_role(context)
            
            if role == "target":
                targets.append(pokemon)
            elif role == "protected":
                protected.append(pokemon)
        
        return {
            "targets": targets,
            "protected": protected,
            "mission_type": mission_type,
            "priority": priority,
            "raw_text": order_text,
            "extracted_pokemon": pokemon_names
        }
    
    def extract_mission_type(self, text: str) -> str:
        """
        Extract mission type from text.
        """
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["neutralize", "eliminate", "destroy"]):
            return "elimination"
        elif any(word in text_lower for word in ["capture", "arrest", "detain"]):
            return "capture"
        elif any(word in text_lower for word in ["investigate", "reconnaissance", "scout"]):
            return "reconnaissance"
        elif any(word in text_lower for word in ["protect", "defend", "guard"]):
            return "protection"
        else:
            return "unknown"
    
    def extract_priority(self, text: str) -> str:
        """
        Extract mission priority from text.
        """
        text_lower = text.lower()
        
        # High priority keywords
        high_priority = ["urgent", "immediately", "asap", "critical", "high-priority", 
                        "high priority", "emergency", "immediate", "right now"]
        
        # Medium priority keywords  
        medium_priority = ["soon", "important", "priority", "significant"]
        
        if any(word in text_lower for word in high_priority):
            return "high"
        elif any(word in text_lower for word in medium_priority):
            return "medium"
        else:
            return "normal"
    
    def classify_pokemon_role(self, context: str) -> str:
        """
        Classify Pokémon role based on context with improved accuracy.
        """
        context_lower = context.lower()
        
        # Enhanced target keywords with weights
        target_keywords = {
            "neutralize": 3, "eliminate": 3, "destroy": 3, "kill": 3, "target": 2,
            "threat": 2, "dangerous": 2, "hostile": 2, "attack": 2, "combat": 2,
            "defeat": 2, "stop": 2, "prevent": 2, "anomalous": 2, "unusual": 2,
            "suspicious": 2, "imminent threat": 4, "must be stopped": 3,
            "take down": 3, "engage": 2, "take out": 2
        }
        
        # Enhanced protected keywords with weights
        protected_keywords = {
            "protect": 3, "care": 2, "don't": 2, "avoid": 3, "spare": 3,
            "safe": 2, "friendly": 2, "ally": 2, "innocent": 3, "civilians": 3,
            "draw into combat": 3, "not to": 2, "remember": 2, "nearby": 1,
            "take care": 2, "preserve": 3, "guard": 2, "defend": 2,
            "keep safe": 3, "do not harm": 4, "do not hit": 4
        }
        
        # Calculate weighted scores
        target_score = sum(weight for keyword, weight in target_keywords.items() 
                          if keyword in context_lower)
        protected_score = sum(weight for keyword, weight in protected_keywords.items() 
                             if keyword in context_lower)
        
        # Improved decision logic
        if target_score > protected_score and target_score > 0:
            return "target"
        elif protected_score > target_score and protected_score > 0:
            return "protected"
        else:
            return "neutral"
    
    def extract_pokemon_names(self, text: str) -> List[str]:
        """
        Enhanced Pokémon name extraction with better pattern matching.
        """
        # Extended Pokémon list (first 151 for demonstration)
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
    
    def get_pokemon_context(self, text: str, pokemon: str) -> str:
        """
        Get context around a Pokémon name with improved window size and multi-species handling.
        """
        pokemon_lower = pokemon.lower()
        text_lower = text.lower()
        
        start_pos = text_lower.find(pokemon_lower)
        if start_pos == -1:
            return ""
        
        # Extract larger context window
        context_start = max(0, start_pos - 150)
        context_end = min(len(text), start_pos + len(pokemon) + 150)
        
        context = text[context_start:context_end]
        
        # For multi-species scenarios, look for connecting words
        context_lower = context.lower()
        if any(connector in context_lower for connector in ["and", "or", "but", "while", "whereas"]):
            # Extend context to include the full sentence
            sentence_start = max(0, context.rfind('.', 0, start_pos - context_start) + 1)
            sentence_end = context.find('.', start_pos - context_start)
            if sentence_end == -1:
                sentence_end = len(context)
            
            return context[sentence_start:sentence_end].strip()
        
        return context
    
    def parse_mission_orders_fallback(self, order_text: str) -> Dict:
        """
        Fallback parsing when spaCy is not available.
        """
        pokemon_names = self.extract_pokemon_names(order_text)
        targets = []
        protected = []
        
        for pokemon in pokemon_names:
            context = self.get_pokemon_context(order_text, pokemon)
            role = self.classify_pokemon_role(context)
            
            if role == "target":
                targets.append(pokemon)
            elif role == "protected":
                protected.append(pokemon)
        
        return {
            "targets": targets,
            "protected": protected,
            "mission_type": self.extract_mission_type(order_text),
            "priority": self.extract_priority(order_text),
            "raw_text": order_text,
            "extracted_pokemon": pokemon_names
        }
    
    def generate_targeting_coordinates(self, image_path: str, mission_orders: str) -> Dict:
        """
        Generate targeting coordinates with enhanced analysis.
        """
        # Parse mission orders
        parsed_orders = self.parse_mission_orders(mission_orders)
        targets = parsed_orders["targets"]
        protected = parsed_orders["protected"]
        
        print(f"Mission Analysis:")
        print(f"  Type: {parsed_orders['mission_type']}")
        print(f"  Priority: {parsed_orders['priority']}")
        print(f"  Target species: {targets}")
        print(f"  Protected species: {protected}")
        
        # Detect Pokémon in image
        detected_pokemon = self.detector.detect_pokemon(image_path)
        print(f"Detected Pokémon: {[p['species'] for p in detected_pokemon]}")
        
        # Generate targeting coordinates
        targeting_coordinates = []
        targeting_details = []
        
        for pokemon in detected_pokemon:
            species = pokemon["species"]
            confidence = pokemon["confidence"]
            
            if species in targets:
                x, y, w, h = pokemon["bounding_box"]
                target_coord = (x + w / 2, y + h / 2)
                targeting_coordinates.append(target_coord)
                
                targeting_details.append({
                    "species": species,
                    "coordinates": target_coord,
                    "confidence": confidence,
                    "bounding_box": pokemon["bounding_box"],
                    "status": "target"
                })
                
                print(f"  ✓ Targeting {species} at {target_coord} (confidence: {confidence:.2f})")
                
            elif species in protected:
                targeting_details.append({
                    "species": species,
                    "coordinates": None,
                    "confidence": confidence,
                    "bounding_box": pokemon["bounding_box"],
                    "status": "protected"
                })
                print(f"  ⚠ Skipping protected species: {species}")
                
            else:
                targeting_details.append({
                    "species": species,
                    "coordinates": None,
                    "confidence": confidence,
                    "bounding_box": pokemon["bounding_box"],
                    "status": "neutral"
                })
                print(f"  - Species {species} not mentioned in mission orders")
        
        # Save mission to history
        mission_record = {
            "timestamp": self.get_timestamp(),
            "orders": parsed_orders,
            "detections": detected_pokemon,
            "targeting": targeting_details
        }
        self.mission_history.append(mission_record)
        
        return {
            "coordinates": targeting_coordinates,
            "details": targeting_details,
            "mission_analysis": parsed_orders,
            "detection_results": detected_pokemon
        }
    
    def get_timestamp(self) -> str:
        """
        Get current timestamp.
        """
        from datetime import datetime
        return datetime.now().isoformat()
    
    def save_mission_report(self, targeting_result: Dict, output_file: str = "enhanced_mission_report.json"):
        """
        Save enhanced mission report.
        """
        report = {
            "mission_summary": {
                "type": targeting_result["mission_analysis"]["mission_type"],
                "priority": targeting_result["mission_analysis"]["priority"],
                "targets": targeting_result["mission_analysis"]["targets"],
                "protected": targeting_result["mission_analysis"]["protected"],
                "targeting_coordinates": targeting_result["coordinates"]
            },
            "targeting_details": targeting_result["details"],
            "detection_results": targeting_result["detection_results"],
            "raw_orders": targeting_result["mission_analysis"]["raw_text"],
            "timestamp": self.get_timestamp()
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Enhanced mission report saved to {output_file}")
    
    def get_mission_history(self) -> List[Dict]:
        """
        Get mission history.
        """
        return self.mission_history
    
    def save_detection_image(self, image_path: str, targeting_result: Dict, output_path: str):
        """
        Save image with detection and targeting information.
        """
        if not os.path.exists(image_path):
            print(f"Image file {image_path} not found")
            return
        
        image = cv2.imread(image_path)
        if image is None:
            print(f"Could not load image {image_path}")
            return
        
        # Draw all detections
        result_image = self.detector.draw_detections(image, targeting_result["detection_results"])
        
        # Draw targeting markers
        for detail in targeting_result["details"]:
            if detail["coordinates"] is not None:
                x, y = detail["coordinates"]
                # Draw targeting crosshair
                cv2.drawMarker(result_image, (int(x), int(y)), (0, 0, 255), 
                             cv2.MARKER_CROSS, 20, 3)
                cv2.putText(result_image, f"TARGET: {detail['species']}", 
                           (int(x) + 25, int(y) - 25), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.6, (0, 0, 255), 2)
        
        cv2.imwrite(output_path, result_image)
        print(f"Targeting image saved to {output_path}")

def main():
    """
    Demonstrate the enhanced targeting system.
    """
    print("=== Enhanced Pokémon Targeting System ===")
    print()
    
    # Initialize enhanced system
    system = EnhancedPokemonTargetingSystem()
    
    # Example mission orders
    mission_orders = """
    URGENT: HQ has detected unusual Bulbasaur activity in Sector 7. Field sensors logged anomalous behavior that suggests an imminent threat to civilian safety.
    Remember there are Pikachu and Charizard nearby — take care not to draw them into combat. 
    You are to neutralize the bulbasaurs immediately. This is a high-priority elimination mission.
    """
    
    # Process mission
    image_path = "battlefield_image.png"
    print("Processing enhanced mission orders...")
    print()
    
    targeting_result = system.generate_targeting_coordinates(image_path, mission_orders)
    
    print(f"\nFinal targeting coordinates: {targeting_result['coordinates']}")
    
    # Save enhanced mission report
    system.save_mission_report(targeting_result)
    
    # Save detection image with targeting markers
    system.save_detection_image(image_path, targeting_result, "enhanced_targeting_result.png")
    
    print("\nEnhanced mission analysis complete!")

if __name__ == "__main__":
    main()

