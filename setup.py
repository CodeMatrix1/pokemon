#!/usr/bin/env python3
"""
Setup script for Pokémon Targeting System
"""

from setuptools import setup, find_packages

setup(
    name="pokemon-targeting-system",
    version="1.0.0",
    description="A system for parsing mission orders and detecting Pokémon in battlefield images",
    author="Pokémon Research Team",
    packages=find_packages(),
    install_requires=[
        "opencv-python>=4.8.0",
        "spacy>=3.7.0",
        "numpy>=1.24.0",
        "Pillow>=10.0.0",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "pokemon-targeting=pokemon_targeting_system:main",
        ],
    },
)

