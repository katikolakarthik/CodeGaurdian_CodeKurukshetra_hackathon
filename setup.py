#!/usr/bin/env python3
"""
Setup script for AI Code Plagiarism Detector.
This script helps set up the environment and install dependencies.
"""

import os
import sys
import subprocess
import platform

def print_header():
    """Print setup header."""
    print("=" * 60)
    print("🔍 AI Code Plagiarism Detector Setup")
    print("=" * 60)
    print()

def check_python_version():
    """Check if Python version is compatible."""
    print("🐍 Checking Python version...")
    
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required.")
        print(f"   Current version: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version.split()[0]} detected")
    return True

def install_dependencies():
    """Install required dependencies."""
    print("\n📦 Installing dependencies...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def check_env_file():
    """Check if .env file exists and is configured."""
    print("\n🔧 Checking environment configuration...")
    
    if not os.path.exists(".env"):
        print("❌ .env file not found")
        print("   Please create a .env file with your API keys")
        return False
    
    # Check if required keys are present
    required_keys = [
        "WATSONX_API_KEY",
        "WATSONX_PROJECT_ID", 
        "HUGGINGFACE_API_TOKEN"
    ]
    
    missing_keys = []
    with open(".env", "r") as f:
        content = f.read()
        for key in required_keys:
            if key not in content or f"{key}=" in content:
                missing_keys.append(key)
    
    if missing_keys:
        print(f"❌ Missing or empty API keys: {', '.join(missing_keys)}")
        print("   Please update your .env file with valid API keys")
        return False
    
    print("✅ Environment configuration looks good")
    return True

def create_directories():
    """Create necessary directories."""
    print("\n📁 Creating directories...")
    
    directories = ["backend", "frontend", "utils", "demo_files"]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ Created directory: {directory}")
        else:
            print(f"ℹ️  Directory already exists: {directory}")

def test_imports():
    """Test if all required modules can be imported."""
    print("\n🧪 Testing imports...")
    
    required_modules = [
        "fastapi",
        "uvicorn", 
        "streamlit",
        "requests",
        "sentence_transformers",
        "faiss",
        "numpy",
        "pandas",
        "plotly",
        "reportlab"
    ]
    
    failed_imports = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n❌ Failed to import: {', '.join(failed_imports)}")
        return False
    
    print("\n✅ All imports successful")
    return True

def print_next_steps():
    """Print next steps for the user."""
    print("\n" + "=" * 60)
    print("🎉 Setup Complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Start the backend server:")
    print("   python start_backend.py")
    print()
    print("2. In a new terminal, start the frontend:")
    print("   python start_frontend.py")
    print()
    print("3. Open your browser and go to:")
    print("   http://localhost:8501")
    print()
    print("4. Test with demo files in the demo_files/ directory")
    print()
    print("📚 For more information, see README.md")

def main():
    """Main setup function."""
    print_header()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed during dependency installation")
        sys.exit(1)
    
    # Test imports
    if not test_imports():
        print("\n❌ Setup failed during import testing")
        sys.exit(1)
    
    # Check environment file
    if not check_env_file():
        print("\n⚠️  Please configure your .env file before running the application")
        print("   See README.md for configuration instructions")
    
    # Print next steps
    print_next_steps()

if __name__ == "__main__":
    main()
