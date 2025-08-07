#!/usr/bin/env python3
"""
Install FastAPI dependencies for the API server
"""

import subprocess
import sys

def install_packages():
    """Install required packages for FastAPI server"""
    packages = [
        "fastapi",
        "uvicorn[standard]",
        "python-multipart",
        "pydantic"
    ]
    
    print("Installing FastAPI dependencies...")
    print("=" * 50)
    
    for package in packages:
        print(f"\nInstalling {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✓ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install {package}: {e}")
            return False
    
    print("\n" + "=" * 50)
    print("All dependencies installed successfully!")
    print("\nTo start the FastAPI server, run:")
    print("  python api_server_fastapi.py")
    print("\nThe server will be available at:")
    print("  http://localhost:5000")
    print("\nInteractive API documentation at:")
    print("  http://localhost:5000/docs")
    return True

if __name__ == "__main__":
    install_packages()