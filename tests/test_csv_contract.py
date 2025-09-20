#!/usr/bin/env python3
"""
Test suite for CSV output contract validation.
Tests exact CSV formatting and schema compliance.
"""

import unittest
import csv
import json
import os
import sys
import tempfile
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from pokemon_targeting_enhanced import EnhancedPokemonTargetingSystem
from tools.validator import load_predictions_csv


class TestCSVContract(unittest.TestCase):
    """Test CSV output contract and schema compliance."""
    
    def setUp(self):
        self.system = EnhancedPokemonTargetingSystem()
    
    def test_csv_schema_compliance(self):
        """Test that CSV output matches the required schema exactly."""
        # Expected CSV schema:
        # image_id,points
        # img_00000.png,"[[x1,y1],[x2,y2]]"
        
        # Create test targeting result
        test_result = {
            "coordinates": [(125.0, 175.0), (250.0, 300.0)],
            "details": [
                {"species": "Bulbasaur", "coordinates": (125.0, 175.0), "status": "target"},
                {"species": "Pikachu", "coordinates": (250.0, 300.0), "status": "target"}
            ]
        }
        
        # Write to temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['image_id', 'points'])
            
            # Format points as JSON string
            points_json = json.dumps(test_result["coordinates"])
            writer.writerow(['img_00000.png', points_json])
            
            temp_file = f.name
        
        try:
            # Load and validate the CSV
            predictions = load_predictions_csv(temp_file)
            
            # Verify schema compliance
            self.assertIn('img_00000.png', predictions)
            self.assertEqual(len(predictions['img_00000.png']), 2)
            self.assertEqual(predictions['img_00000.png'][0], (125.0, 175.0))
            self.assertEqual(predictions['img_00000.png'][1], (250.0, 300.0))
            
        finally:
            os.unlink(temp_file)
    
    def test_csv_with_empty_points(self):
        """Test CSV handling with empty points list."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['image_id', 'points'])
            writer.writerow(['img_00001.png', '[]'])
            temp_file = f.name
        
        try:
            predictions = load_predictions_csv(temp_file)
            self.assertIn('img_00001.png', predictions)
            self.assertEqual(len(predictions['img_00001.png']), 0)
            
        finally:
            os.unlink(temp_file)
    
    def test_csv_with_single_point(self):
        """Test CSV handling with single point."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['image_id', 'points'])
            writer.writerow(['img_00002.png', '[[100.5, 200.5]]'])
            temp_file = f.name
        
        try:
            predictions = load_predictions_csv(temp_file)
            self.assertIn('img_00002.png', predictions)
            self.assertEqual(len(predictions['img_00002.png']), 1)
            self.assertEqual(predictions['img_00002.png'][0], (100.5, 200.5))
            
        finally:
            os.unlink(temp_file)
    
    def test_csv_with_invalid_format(self):
        """Test CSV handling with invalid format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['image_id', 'points'])
            writer.writerow(['img_00003.png', 'invalid_json'])
            temp_file = f.name
        
        try:
            with self.assertRaises(ValueError):
                load_predictions_csv(temp_file)
                
        finally:
            os.unlink(temp_file)
    
    def test_csv_missing_columns(self):
        """Test CSV handling with missing required columns."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['image_id'])  # Missing 'points' column
            writer.writerow(['img_00004.png'])
            temp_file = f.name
        
        try:
            with self.assertRaises(ValueError):
                load_predictions_csv(temp_file)
                
        finally:
            os.unlink(temp_file)
    
    def test_csv_with_invalid_coordinates(self):
        """Test CSV handling with invalid coordinate format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['image_id', 'points'])
            writer.writerow(['img_00005.png', '[[100, 200, 300]]'])  # 3 coordinates instead of 2
            temp_file = f.name
        
        try:
            predictions = load_predictions_csv(temp_file)
            # Invalid coordinates should be filtered out
            self.assertIn('img_00005.png', predictions)
            self.assertEqual(len(predictions['img_00005.png']), 0)
            
        finally:
            os.unlink(temp_file)
    
    def test_csv_with_non_numeric_coordinates(self):
        """Test CSV handling with non-numeric coordinates."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['image_id', 'points'])
            writer.writerow(['img_00006.png', '[["x", "y"]]'])  # Non-numeric coordinates
            temp_file = f.name
        
        try:
            predictions = load_predictions_csv(temp_file)
            # Invalid coordinates should be filtered out
            self.assertIn('img_00006.png', predictions)
            self.assertEqual(len(predictions['img_00006.png']), 0)
            
        finally:
            os.unlink(temp_file)
    
    def test_multiple_images_csv(self):
        """Test CSV with multiple images."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['image_id', 'points'])
            writer.writerow(['img_00000.png', '[[100, 200]]'])
            writer.writerow(['img_00001.png', '[[150, 250], [300, 400]]'])
            writer.writerow(['img_00002.png', '[]'])
            temp_file = f.name
        
        try:
            predictions = load_predictions_csv(temp_file)
            
            self.assertEqual(len(predictions), 3)
            self.assertEqual(predictions['img_00000.png'], [(100.0, 200.0)])
            self.assertEqual(predictions['img_00001.png'], [(150.0, 250.0), (300.0, 400.0)])
            self.assertEqual(predictions['img_00002.png'], [])
            
        finally:
            os.unlink(temp_file)
    
    def test_coordinate_precision(self):
        """Test that coordinates maintain proper precision."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['image_id', 'points'])
            writer.writerow(['img_00007.png', '[[123.456789, 987.654321]]'])
            temp_file = f.name
        
        try:
            predictions = load_predictions_csv(temp_file)
            
            self.assertIn('img_00007.png', predictions)
            coord = predictions['img_00007.png'][0]
            self.assertAlmostEqual(coord[0], 123.456789, places=6)
            self.assertAlmostEqual(coord[1], 987.654321, places=6)
            
        finally:
            os.unlink(temp_file)
    
    def test_image_id_format_validation(self):
        """Test validation of image ID format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['image_id', 'points'])
            
            # Test various image ID formats
            test_cases = [
                'img_00000.png',
                'IMG_00001.PNG',
                'image_001.jpg',
                'frame_123.tiff',
                'test_image.bmp'
            ]
            
            for img_id in test_cases:
                writer.writerow([img_id, '[[100, 200]]'])
            
            temp_file = f.name
        
        try:
            predictions = load_predictions_csv(temp_file)
            
            # All image IDs should be loaded (format validation is lenient)
            for img_id in test_cases:
                self.assertIn(img_id, predictions)
                self.assertEqual(len(predictions[img_id]), 1)
                
        finally:
            os.unlink(temp_file)
    
    def test_csv_whitespace_handling(self):
        """Test CSV handling with whitespace in data."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['image_id', 'points'])
            writer.writerow(['  img_00008.png  ', '  [[100, 200]]  '])  # Extra whitespace
            temp_file = f.name
        
        try:
            predictions = load_predictions_csv(temp_file)
            
            # Whitespace should be stripped
            self.assertIn('img_00008.png', predictions)
            self.assertEqual(predictions['img_00008.png'], [(100.0, 200.0)])
            
        finally:
            os.unlink(temp_file)
    
    def test_csv_encoding_handling(self):
        """Test CSV handling with different encodings."""
        # Test UTF-8 encoding (default)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['image_id', 'points'])
            writer.writerow(['img_00009.png', '[[100, 200]]'])
            temp_file = f.name
        
        try:
            predictions = load_predictions_csv(temp_file)
            self.assertIn('img_00009.png', predictions)
            
        finally:
            os.unlink(temp_file)
    
    def test_csv_file_not_found(self):
        """Test handling of non-existent CSV file."""
        with self.assertRaises(FileNotFoundError):
            load_predictions_csv('nonexistent_file.csv')
    
    def test_csv_empty_file(self):
        """Test handling of empty CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            # Empty file
            temp_file = f.name
        
        try:
            with self.assertRaises(StopIteration):
                load_predictions_csv(temp_file)
                
        finally:
            os.unlink(temp_file)
    
    def test_csv_header_only(self):
        """Test handling of CSV with only headers."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['image_id', 'points'])
            temp_file = f.name
        
        try:
            predictions = load_predictions_csv(temp_file)
            self.assertEqual(len(predictions), 0)
            
        finally:
            os.unlink(temp_file)


if __name__ == "__main__":
    unittest.main()

