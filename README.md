# Pokémon Targeting System

A Python-based system that combines Natural Language Processing (NLP) and Computer Vision (CV) to parse mission orders and detect Pokémon in battlefield images for tactical targeting.

## Features

- **NLP Module**: Parses HQ mission orders to extract target and protected species
- **CV Module**: Detects Pokémon in battlefield images (currently using dummy data)
- **Targeting Logic**: Integrates mission orders with image detection to generate targeting coordinates
- **Mission Reporting**: Saves detailed mission reports in JSON format

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Download the spaCy English model:

```bash
python -m spacy download en_core_web_sm
```

## Usage

### Basic Usage

```python
from pokemon_targeting_system import generate_targeting_coordinates

# Define mission orders
mission_orders = """
HQ has detected unusual Bulbasaur activity in the area. Field sensors logged anomalous behavior that suggests an imminent threat.
Remember there are Pikachu and Charizard nearby — take care not to draw them into combat. 
You are to neutralize the bulbasaurs immediately.
"""

# Generate targeting coordinates
coordinates = generate_targeting_coordinates("battlefield_image.png", mission_orders)
print(coordinates)
```

### Running the Example

```bash
python pokemon_targeting_system.py
```

## System Components

### 1. NLP Module (`parse_mission_orders`)

- Extracts Pokémon names from mission text
- Uses context analysis to determine if species are targets or protected
- Supports fallback parsing when spaCy is not available
- Recognizes common mission order patterns and keywords

### 2. CV Module (`detect_pokemon_in_image`)

- Currently uses dummy detection data for demonstration
- Designed to integrate with object detection models (YOLO, Faster R-CNN)
- Returns bounding boxes and species labels
- Includes confidence scores for detections

### 3. Targeting Logic (`generate_targeting_coordinates`)

- Combines parsed mission orders with image detections
- Filters detections based on mission requirements
- Calculates targeting coordinates (center of bounding boxes)
- Provides detailed logging of targeting decisions

## Mission Order Format

The system recognizes common patterns in mission orders:

**Target Species Keywords:**
- neutralize, eliminate, destroy, target, threat, dangerous
- hostile, attack, combat, defeat, stop, prevent
- anomalous, unusual, suspicious, imminent threat

**Protected Species Keywords:**
- protect, care, don't, avoid, spare, safe
- friendly, ally, innocent, civilians
- draw into combat, not to, remember, nearby

## Example Mission Orders

```
HQ has detected unusual Bulbasaur activity in the area. Field sensors logged anomalous behavior that suggests an imminent threat.
Remember there are Pikachu and Charizard nearby — take care not to draw them into combat. 
You are to neutralize the bulbasaurs immediately.
```

This would result in:
- **Targets**: Bulbasaur
- **Protected**: Pikachu, Charizard
- **Action**: Generate targeting coordinates for Bulbasaur only

## Output

The system generates:
1. **Targeting Coordinates**: List of (x, y) coordinates for targeting
2. **Mission Report**: Detailed JSON report with analysis results
3. **Console Output**: Real-time logging of targeting decisions

## Future Enhancements

- [ ] Integrate real object detection models (YOLO, Faster R-CNN)
- [ ] Expand Pokémon name recognition database
- [ ] Add support for more complex mission order formats
- [ ] Implement image preprocessing and enhancement
- [ ] Add confidence scoring for targeting decisions
- [ ] Support for video input and real-time processing

## Dependencies

- OpenCV (cv2) - Computer vision operations
- spaCy - Natural language processing
- NumPy - Numerical operations
- Pillow - Image processing

## License

This project is for educational and research purposes.

