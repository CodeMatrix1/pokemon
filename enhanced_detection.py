#!/usr/bin/env python3
"""
Enhanced Pokémon Detection Module
This module provides improved object detection capabilities using YOLO and other advanced techniques.
"""

import cv2
import numpy as np
import json
import os
from typing import List, Dict, Tuple, Optional
import requests
from pathlib import Path

class PokemonDetector:
    """
    Enhanced Pokémon detector using YOLO and other computer vision techniques.
    """
    
    def __init__(self, model_path: Optional[str] = None, confidence_threshold: float = 0.5):
        """
        Initialize the Pokémon detector.
        
        :param model_path: Path to YOLO model files (optional)
        :param confidence_threshold: Minimum confidence for detections
        """
        self.confidence_threshold = confidence_threshold
        self.model_path = model_path
        self.net = None
        self.classes = []
        self.colors = []
        
        # Initialize with dummy data if no model is provided
        if model_path and os.path.exists(model_path):
            self.load_yolo_model(model_path)
        else:
            self.setup_dummy_detector()
    
    def load_yolo_model(self, model_path: str):
        """
        Load YOLO model for object detection.
        """
        try:
            # Load YOLO model
            weights_path = os.path.join(model_path, "yolov3.weights")
            config_path = os.path.join(model_path, "yolov3.cfg")
            names_path = os.path.join(model_path, "coco.names")
            
            if all(os.path.exists(p) for p in [weights_path, config_path, names_path]):
                self.net = cv2.dnn.readNet(weights_path, config_path)
                
                # Load class names
                with open(names_path, 'r') as f:
                    self.classes = [line.strip() for line in f.readlines()]
                
                # Generate random colors for each class
                self.colors = np.random.uniform(0, 255, size=(len(self.classes), 3))
                print(f"YOLO model loaded successfully with {len(self.classes)} classes")
            else:
                print("YOLO model files not found, using dummy detector")
                self.setup_dummy_detector()
                
        except Exception as e:
            print(f"Error loading YOLO model: {e}")
            self.setup_dummy_detector()
    
    def setup_dummy_detector(self):
        """
        Setup dummy detector for demonstration purposes.
        """
        self.classes = ["Bulbasaur", "Pikachu", "Charizard", "Squirtle", "Eevee", "Mewtwo"]
        self.colors = np.random.uniform(0, 255, size=(len(self.classes), 3))
        print("Using dummy detector for demonstration")
    
    def detect_pokemon(self, image_path: str) -> List[Dict]:
        """
        Detect Pokémon in an image.
        
        :param image_path: Path to the image file
        :return: List of detected Pokémon with bounding boxes and confidence scores
        """
        if not os.path.exists(image_path):
            print(f"Image file {image_path} not found, using dummy detections")
            return self.get_dummy_detections()
        
        image = cv2.imread(image_path)
        if image is None:
            print(f"Could not load image {image_path}, using dummy detections")
            return self.get_dummy_detections()
        
        if self.net is not None:
            return self.detect_with_yolo(image)
        else:
            return self.detect_with_dummy(image)
    
    def detect_with_yolo(self, image: np.ndarray) -> List[Dict]:
        """
        Detect Pokémon using YOLO model.
        """
        height, width = image.shape[:2]
        
        # Prepare image for YOLO
        blob = cv2.dnn.blobFromImage(image, 1/255.0, (416, 416), swapRB=True, crop=False)
        self.net.setInput(blob)
        
        # Get detections
        layer_names = self.net.getLayerNames()
        output_layers = [layer_names[i[0] - 1] for i in self.net.getUnconnectedOutLayers()]
        outputs = self.net.forward(output_layers)
        
        # Process detections
        detections = []
        boxes = []
        confidences = []
        class_ids = []
        
        for output in outputs:
            for detection in output:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                
                if confidence > self.confidence_threshold:
                    # Get bounding box coordinates
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)
                    
                    # Convert to top-left corner coordinates
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)
                    
                    boxes.append([x, y, w, h])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)
        
        # Apply non-maximum suppression
        indices = cv2.dnn.NMSBoxes(boxes, confidences, self.confidence_threshold, 0.4)
        
        if len(indices) > 0:
            for i in indices.flatten():
                x, y, w, h = boxes[i]
                class_id = class_ids[i]
                confidence = confidences[i]
                
                # Map YOLO classes to Pokémon (this is a simplified mapping)
                pokemon_name = self.map_yolo_class_to_pokemon(class_id)
                
                detections.append({
                    "species": pokemon_name,
                    "bounding_box": [x, y, w, h],
                    "confidence": confidence,
                    "class_id": class_id
                })
        
        return detections
    
    def map_yolo_class_to_pokemon(self, class_id: int) -> str:
        """
        Map YOLO COCO class IDs to Pokémon names.
        This is a simplified mapping for demonstration.
        """
        # COCO class mapping (simplified)
        coco_to_pokemon = {
            0: "Pikachu",    # person -> Pikachu
            1: "Charizard",  # bicycle -> Charizard
            2: "Bulbasaur",  # car -> Bulbasaur
            3: "Squirtle",   # motorcycle -> Squirtle
            4: "Eevee",      # airplane -> Eevee
            5: "Mewtwo"      # bus -> Mewtwo
        }
        
        return coco_to_pokemon.get(class_id, "Unknown")
    
    def detect_with_dummy(self, image: np.ndarray) -> List[Dict]:
        """
        Detect Pokémon using dummy detection (for demonstration).
        """
        height, width = image.shape[:2]
        
        # Generate random detections based on image size
        num_detections = np.random.randint(1, 4)
        detections = []
        
        for i in range(num_detections):
            # Random position and size
            x = np.random.randint(0, width - 100)
            y = np.random.randint(0, height - 100)
            w = np.random.randint(50, 100)
            h = np.random.randint(50, 100)
            
            # Random Pokémon
            species = np.random.choice(self.classes)
            confidence = np.random.uniform(0.7, 0.95)
            
            detections.append({
                "species": species,
                "bounding_box": [x, y, w, h],
                "confidence": confidence
            })
        
        return detections
    
    def get_dummy_detections(self) -> List[Dict]:
        """
        Get dummy detections for testing.
        """
        return [
            {
                "species": "Bulbasaur",
                "bounding_box": [100, 150, 50, 50],
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
    
    def draw_detections(self, image: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """
        Draw bounding boxes and labels on the image.
        
        :param image: Input image
        :param detections: List of detections
        :return: Image with drawn detections
        """
        result_image = image.copy()
        
        for detection in detections:
            x, y, w, h = detection["bounding_box"]
            species = detection["species"]
            confidence = detection["confidence"]
            
            # Draw bounding box
            cv2.rectangle(result_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Draw label
            label = f"{species}: {confidence:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            
            # Draw label background
            cv2.rectangle(result_image, (x, y - label_size[1] - 10), 
                         (x + label_size[0], y), (0, 255, 0), -1)
            
            # Draw label text
            cv2.putText(result_image, label, (x, y - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
        
        return result_image
    
    def save_detection_image(self, image_path: str, detections: List[Dict], output_path: str):
        """
        Save image with detections drawn.
        
        :param image_path: Path to original image
        :param detections: List of detections
        :param output_path: Path to save the result image
        """
        if not os.path.exists(image_path):
            print(f"Original image {image_path} not found")
            return
        
        image = cv2.imread(image_path)
        if image is None:
            print(f"Could not load image {image_path}")
            return
        
        result_image = self.draw_detections(image, detections)
        cv2.imwrite(output_path, result_image)
        print(f"Detection image saved to {output_path}")

def download_yolo_model(model_dir: str = "yolo_model"):
    """
    Download YOLO model files (simplified version for demonstration).
    """
    os.makedirs(model_dir, exist_ok=True)
    
    # In a real implementation, you would download the actual YOLO model files
    # For now, we'll just create placeholder files
    print(f"YOLO model directory created at {model_dir}")
    print("In a real implementation, you would download:")
    print("- yolov3.weights")
    print("- yolov3.cfg") 
    print("- coco.names")
    
    return model_dir

def main():
    """
    Demonstrate the enhanced detection system.
    """
    print("=== Enhanced Pokémon Detection System ===")
    
    # Initialize detector
    detector = PokemonDetector()
    
    # Test with dummy image
    test_image = "test_battlefield.png"
    detections = detector.detect_pokemon(test_image)
    
    print(f"Detected {len(detections)} Pokémon:")
    for detection in detections:
        print(f"  {detection['species']}: {detection['confidence']:.2f} at {detection['bounding_box']}")
    
    # Save detection results
    if os.path.exists(test_image):
        detector.save_detection_image(test_image, detections, "detection_result.png")
    
    # Save detection data
    with open("detection_results.json", "w") as f:
        json.dump(detections, f, indent=2)
    
    print("Detection results saved to detection_results.json")

if __name__ == "__main__":
    main()

