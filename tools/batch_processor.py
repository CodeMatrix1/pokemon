#!/usr/bin/env python3
"""
Pokemon: Tactical Strike - Batch Processing Pipeline
Processes folder of images + per-image orders JSON → CSV outputs
"""

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from pokemon_targeting_enhanced import EnhancedPokemonTargetingSystem
from tools.validator import VALID_CLASS_IDS


class BatchProcessor:
    """Batch processor for Pokemon targeting system."""
    
    def __init__(self, model_path: str = None):
        """
        Initialize batch processor.
        
        :param model_path: Path to detection model (optional)
        """
        self.system = EnhancedPokemonTargetingSystem(model_path)
        self.results = []
    
    def load_orders(self, orders_path: str) -> Dict[str, str]:
        """
        Load per-image orders from JSON file.
        
        :param orders_path: Path to orders JSON file
        :return: Dictionary mapping image_id to order text
        """
        with open(orders_path, 'r', encoding='utf-8') as f:
            orders = json.load(f)
        
        # Ensure all values are strings
        return {k: str(v) for k, v in orders.items()}
    
    def process_single_image(self, image_path: str, orders: str) -> Dict:
        """
        Process a single image with given orders.
        
        :param image_path: Path to image file
        :param orders: Mission orders text
        :return: Processing result dictionary
        """
        try:
            result = self.system.generate_targeting_coordinates(image_path, orders)
            
            # Extract coordinates in the required format
            coordinates = result['coordinates']
            
            # Validate coordinates are within image bounds
            if os.path.exists(image_path):
                # Load image to get dimensions (simplified)
                import cv2
                img = cv2.imread(image_path)
                if img is not None:
                    height, width = img.shape[:2]
                    validated_coords = []
                    for x, y in coordinates:
                        if 0 <= x <= width and 0 <= y <= height:
                            validated_coords.append([float(x), float(y)])
                        else:
                            print(f"Warning: Coordinate ({x}, {y}) outside image bounds ({width}x{height})")
                    coordinates = validated_coords
            
            return {
                'image_id': os.path.basename(image_path),
                'coordinates': coordinates,
                'success': True,
                'error': None,
                'mission_analysis': result['mission_analysis'],
                'detection_count': len(result['detection_results'])
            }
            
        except Exception as e:
            return {
                'image_id': os.path.basename(image_path),
                'coordinates': [],
                'success': False,
                'error': str(e),
                'mission_analysis': None,
                'detection_count': 0
            }
    
    def process_batch(self, images_dir: str, orders_path: str, output_csv: str) -> Dict:
        """
        Process batch of images with per-image orders.
        
        :param images_dir: Directory containing images
        :param orders_path: Path to orders JSON file
        :param output_csv: Path to output CSV file
        :return: Processing summary
        """
        print(f"Processing batch: {images_dir}")
        print(f"Orders: {orders_path}")
        print(f"Output: {output_csv}")
        
        # Load orders
        orders = self.load_orders(orders_path)
        print(f"Loaded orders for {len(orders)} images")
        
        # Find image files
        image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}
        image_files = []
        
        for ext in image_extensions:
            image_files.extend(Path(images_dir).glob(f'*{ext}'))
            image_files.extend(Path(images_dir).glob(f'*{ext.upper()}'))
        
        if not image_files:
            raise ValueError(f"No image files found in {images_dir}")
        
        print(f"Found {len(image_files)} image files")
        
        # Process each image
        results = []
        successful = 0
        failed = 0
        
        for image_file in sorted(image_files):
            image_id = image_file.name
            
            # Get orders for this image (fallback to default)
            image_orders = orders.get(image_id, orders.get('_default', ''))
            
            print(f"Processing {image_id}...")
            result = self.process_single_image(str(image_file), image_orders)
            results.append(result)
            
            if result['success']:
                successful += 1
                print(f"  ✓ Success: {len(result['coordinates'])} targets")
            else:
                failed += 1
                print(f"  ✗ Failed: {result['error']}")
        
        # Write CSV output
        self.write_csv_output(results, output_csv)
        
        # Generate summary
        summary = {
            'total_images': len(image_files),
            'successful': successful,
            'failed': failed,
            'success_rate': successful / len(image_files) if image_files else 0,
            'total_targets': sum(len(r['coordinates']) for r in results if r['success'])
        }
        
        print(f"\nBatch Processing Complete:")
        print(f"  Total images: {summary['total_images']}")
        print(f"  Successful: {summary['successful']}")
        print(f"  Failed: {summary['failed']}")
        print(f"  Success rate: {summary['success_rate']:.1%}")
        print(f"  Total targets: {summary['total_targets']}")
        
        return summary
    
    def write_csv_output(self, results: List[Dict], output_csv: str):
        """
        Write results to CSV file in the required format.
        
        :param results: List of processing results
        :param output_csv: Path to output CSV file
        """
        os.makedirs(os.path.dirname(output_csv), exist_ok=True)
        
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['image_id', 'points'])
            
            for result in results:
                image_id = result['image_id']
                coordinates = result['coordinates']
                
                # Format coordinates as JSON string
                points_json = json.dumps(coordinates)
                writer.writerow([image_id, points_json])
        
        print(f"CSV output written to: {output_csv}")
    
    def validate_species_constraints(self, results: List[Dict]) -> Dict:
        """
        Validate that only the 4 required species are used.
        
        :param results: List of processing results
        :return: Validation summary
        """
        species_found = set()
        invalid_species = set()
        
        for result in results:
            if result['mission_analysis']:
                # Check extracted species
                extracted = result['mission_analysis'].get('extracted_pokemon', [])
                for species in extracted:
                    species_found.add(species)
                
                # Check targets and protected
                targets = result['mission_analysis'].get('targets', [])
                protected = result['mission_analysis'].get('protected', [])
                
                for species in targets + protected:
                    species_found.add(species)
        
        # Map species names to IDs (simplified mapping)
        species_to_id = {
            'Pikachu': 1, 'Charizard': 2, 'Bulbasaur': 3, 'Mewtwo': 4,
            'pikachu': 1, 'charizard': 2, 'bulbasaur': 3, 'mewtwo': 4
        }
        
        for species in species_found:
            if species not in species_to_id:
                invalid_species.add(species)
        
        validation = {
            'total_species_found': len(species_found),
            'valid_species': species_found - invalid_species,
            'invalid_species': invalid_species,
            'compliance': len(invalid_species) == 0
        }
        
        if invalid_species:
            print(f"⚠️  WARNING: Invalid species found: {invalid_species}")
        else:
            print(f"✅ Species constraint validation passed")
        
        return validation


def main():
    """Main function for batch processing."""
    parser = argparse.ArgumentParser(description='Pokemon Targeting Batch Processor')
    parser.add_argument('--images', required=True, help='Directory containing images')
    parser.add_argument('--orders', required=True, help='Path to orders JSON file')
    parser.add_argument('--output', required=True, help='Path to output CSV file')
    parser.add_argument('--model', help='Path to detection model (optional)')
    parser.add_argument('--validate', action='store_true', help='Run species constraint validation')
    
    args = parser.parse_args()
    
    # Validate inputs
    if not os.path.exists(args.images):
        print(f"Error: Images directory not found: {args.images}")
        sys.exit(1)
    
    if not os.path.exists(args.orders):
        print(f"Error: Orders file not found: {args.orders}")
        sys.exit(1)
    
    try:
        # Initialize processor
        processor = BatchProcessor(args.model)
        
        # Process batch
        summary = processor.process_batch(args.images, args.orders, args.output)
        
        # Run validation if requested
        if args.validate:
            print("\nRunning species constraint validation...")
            # Load results for validation
            results = []
            with open(args.orders, 'r') as f:
                orders = json.load(f)
            
            for image_file in Path(args.images).glob('*'):
                if image_file.suffix.lower() in {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}:
                    image_id = image_file.name
                    image_orders = orders.get(image_id, orders.get('_default', ''))
                    
                    # Process to get mission analysis
                    result = processor.process_single_image(str(image_file), image_orders)
                    results.append(result)
            
            validation = processor.validate_species_constraints(results)
            
            if not validation['compliance']:
                print(f"❌ Species constraint validation FAILED")
                sys.exit(1)
            else:
                print(f"✅ Species constraint validation PASSED")
        
        print(f"\n✅ Batch processing completed successfully!")
        
    except Exception as e:
        print(f"❌ Batch processing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

