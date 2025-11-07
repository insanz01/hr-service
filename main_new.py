"""
HR Screening System - Main Application Entry Point
Restructured version with modular architecture
"""

import os
import sys

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import Flask app from routes module
from src.api.routes import app

if __name__ == "__main__":
    # Set environment variables
    os.environ.setdefault("PYTHONPATH", os.path.join(os.getcwd(), 'src'))

    # Run the application
    app.run(host="0.0.0.0", port=5000, debug=True)