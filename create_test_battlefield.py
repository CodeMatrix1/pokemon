#!/usr/bin/env python3
"""
Create a test battlefield image that matches the mission context example.
This creates a visual representation of the scenario described in the HQ orders.
"""

import cv2
import numpy as np
import os

def create_battlefield_image():
    """Create a test battlefield image with Pokemon placements matching the mission context."""
    
    # Create base battlefield (600x800 pixels)
    width, height = 800, 600
    battlefield = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Set background to brown field color
    battlefield[:] = (139, 69, 19)  # Brown color
    
    # Add some texture/noise to make it look more realistic
    noise = np.random.randint(-20, 20, battlefield.shape, dtype=np.int16)
    battlefield = np.clip(battlefield.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    
    # Add hay bales (brown rectangles)
    # Large hay bale in lower center
    cv2.rectangle(battlefield, (350, 450), (450, 550), (101, 67, 33), -1)
    cv2.rectangle(battlefield, (350, 450), (450, 550), (139, 69, 19), 2)
    
    # Smaller hay bale in upper left
    cv2.rectangle(battlefield, (100, 100), (180, 180), (101, 67, 33), -1)
    cv2.rectangle(battlefield, (100, 100), (180, 180), (139, 69, 19), 2)
    
    # Smaller hay bale in upper right
    cv2.rectangle(battlefield, (620, 120), (700, 200), (101, 67, 33), -1)
    cv2.rectangle(battlefield, (620, 120), (700, 200), (139, 69, 19), 2)
    
    # Add Pokemon at specific locations based on the mission context
    # Expected coordinates: [[438.7, 337.75], [96.81, 382.1], [24.88, 30.69]]
    
    # Bulbasaur 1: Target at (438.7, 337.75) - near center
    cv2.circle(battlefield, (439, 338), 15, (34, 139, 34), -1)  # Green body
    cv2.circle(battlefield, (439, 338), 18, (0, 100, 0), 2)    # Green outline
    cv2.putText(battlefield, "B", (434, 343), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # Bulbasaur 2: Target at (96.81, 382.1) - near left hay bale
    cv2.circle(battlefield, (97, 382), 12, (34, 139, 34), -1)  # Green body
    cv2.circle(battlefield, (97, 382), 15, (0, 100, 0), 2)     # Green outline
    cv2.putText(battlefield, "B", (92, 387), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
    
    # Bulbasaur 3: Target at (24.88, 30.69) - upper left corner
    cv2.circle(battlefield, (25, 31), 10, (34, 139, 34), -1)   # Green body
    cv2.circle(battlefield, (25, 31), 13, (0, 100, 0), 2)      # Green outline
    cv2.putText(battlefield, "B", (20, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 2)
    
    # Protected Pokemon (should not be targeted)
    
    # Charizard: Protected species - large one in lower center
    cv2.circle(battlefield, (400, 500), 20, (255, 140, 0), -1)  # Orange body
    cv2.circle(battlefield, (400, 500), 23, (255, 69, 0), 2)    # Orange outline
    cv2.putText(battlefield, "C", (395, 505), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Charizard: Protected species - smaller one upper left
    cv2.circle(battlefield, (150, 150), 15, (255, 140, 0), -1)  # Orange body
    cv2.circle(battlefield, (150, 150), 18, (255, 69, 0), 2)    # Orange outline
    cv2.putText(battlefield, "C", (145, 155), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # Pikachu: Protected species - upper right
    cv2.circle(battlefield, (650, 150), 12, (255, 255, 0), -1)  # Yellow body
    cv2.circle(battlefield, (650, 150), 15, (255, 215, 0), 2)   # Yellow outline
    cv2.putText(battlefield, "P", (645, 155), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
    
    # Pikachu: Protected species - near upper left hay bale
    cv2.circle(battlefield, (120, 200), 10, (255, 255, 0), -1)  # Yellow body
    cv2.circle(battlefield, (120, 200), 13, (255, 215, 0), 2)   # Yellow outline
    cv2.putText(battlefield, "P", (115, 205), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
    
    # Add some terrain features for realism
    # Add grass patches
    for i in range(0, width, 50):
        for j in range(0, height, 50):
            if np.random.random() > 0.7:
                cv2.circle(battlefield, (i, j), 3, (34, 139, 34), -1)
    
    # Add some rocks/debris
    rock_positions = [(200, 300), (600, 400), (300, 200), (500, 100)]
    for x, y in rock_positions:
        cv2.circle(battlefield, (x, y), 8, (105, 105, 105), -1)
        cv2.circle(battlefield, (x, y), 10, (169, 169, 169), 1)
    
    return battlefield

def main():
    """Create and save the test battlefield image."""
    
    print("🎨 Creating test battlefield image...")
    
    # Create the battlefield
    battlefield = create_battlefield_image()
    
    # Ensure test_data directory exists
    os.makedirs("test_data", exist_ok=True)
    
    # Save the image
    image_path = "test_data/sample_battlefield.png"
    cv2.imwrite(image_path, battlefield)
    
    print(f"✅ Test battlefield created: {image_path}")
    print(f"   Image size: {battlefield.shape[1]}x{battlefield.shape[0]} pixels")
    print("   Contains:")
    print("   - 3 Bulbasaur targets (green circles with 'B')")
    print("   - 2 Charizard protected (orange circles with 'C')")
    print("   - 2 Pikachu protected (yellow circles with 'P')")
    print("   - Hay bales and terrain features")
    
    return image_path

if __name__ == "__main__":
    main()
