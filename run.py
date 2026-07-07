"""
Launch script for the NC Financial Planning Platform.
Run from the project root: python run.py
"""
import sys
from pathlib import Path

# Ensure the project root is on sys.path so 'planner' is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

from planner.app import app

if __name__ == "__main__":
    print("Starting NC Financial Planning Platform...")
    print("Open http://127.0.0.1:8050 in your browser.")
    app.run(debug=True, port=8050)
