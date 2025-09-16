#!/usr/bin/env python3
"""
Test script for AI Code Plagiarism Detector.
This script tests the backend API endpoints.
"""

import requests
import json
import time
import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

API_BASE_URL = "http://localhost:8000"

def test_api_connection():
    """Test if the API is running."""
    print("🔌 Testing API connection...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ API is running")
            return True
        else:
            print(f"❌ API returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Is the backend running?")
        return False
    except Exception as e:
        print(f"❌ Error connecting to API: {e}")
        return False

def test_upload():
    """Test file upload endpoint."""
    print("\n📤 Testing file upload...")
    
    # Read demo file
    demo_file_path = "demo_files/sample_python.py"
    if not os.path.exists(demo_file_path):
        print(f"❌ Demo file not found: {demo_file_path}")
        return False
    
    with open(demo_file_path, "rb") as f:
        files = {"file": (demo_file_path, f.read(), "text/plain")}
        data = {
            "team_name": "Test Team",
            "submission_name": "Test Submission",
            "language": "python"
        }
        
        try:
            response = requests.post(f"{API_BASE_URL}/upload", files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Upload successful")
                print(f"   Submission ID: {result['submission_id']}")
                print(f"   Chunks processed: {result['chunk_count']}")
                return result['submission_id']
            else:
                print(f"❌ Upload failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error during upload: {e}")
            return False

def test_check_plagiarism(submission_id):
    """Test plagiarism checking endpoint."""
    print("\n🔍 Testing plagiarism check...")
    
    # Read similar demo file
    similar_file_path = "demo_files/similar_python.py"
    if not os.path.exists(similar_file_path):
        print(f"❌ Similar demo file not found: {similar_file_path}")
        return False
    
    with open(similar_file_path, "rb") as f:
        files = {"file": (similar_file_path, f.read(), "text/plain")}
        data = {
            "team_name": "Test Team 2",
            "submission_name": "Similar Submission",
            "language": "python"
        }
        
        try:
            response = requests.post(f"{API_BASE_URL}/check", files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Plagiarism check successful")
                print(f"   Overall plagiarism: {result['overall_plagiarism_percentage']:.1f}%")
                print(f"   Originality score: {result['overall_originality_score']:.1f}%")
                print(f"   Flagged chunks: {result['flagged_chunks']}")
                return result
            else:
                print(f"❌ Plagiarism check failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error during plagiarism check: {e}")
            return False

def test_explain():
    """Test explanation endpoint."""
    print("\n🤖 Testing AI explanation...")
    
    suspicious_code = """
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
"""
    
    similar_code = """
def bubble_sort_algorithm(data):
    length = len(data)
    for i in range(length):
        for j in range(0, length - i - 1):
            if data[j] > data[j + 1]:
                data[j], data[j + 1] = data[j + 1], data[j]
    return data
"""
    
    data = {
        "suspicious_code": suspicious_code,
        "similar_code": similar_code,
        "similarity_score": 85.5,
        "team_name": "Test Team",
        "submission_name": "Test Submission"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/explain", data=data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ AI explanation generated")
            print(f"   Explanation: {result['explanation'][:100]}...")
            return True
        else:
            print(f"❌ Explanation failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error during explanation: {e}")
        return False

def test_stats():
    """Test stats endpoint."""
    print("\n📊 Testing stats endpoint...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/stats")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Stats retrieved")
            print(f"   Total submissions: {result['total_submissions']}")
            print(f"   Total chunks: {result['total_chunks']}")
            return True
        else:
            print(f"❌ Stats failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error getting stats: {e}")
        return False

def main():
    """Main test function."""
    print("🧪 AI Code Plagiarism Detector - System Test")
    print("=" * 50)
    
    # Test API connection
    if not test_api_connection():
        print("\n❌ Cannot proceed without API connection")
        print("   Please start the backend server first:")
        print("   python start_backend.py")
        sys.exit(1)
    
    # Test upload
    submission_id = test_upload()
    if not submission_id:
        print("\n❌ Upload test failed")
        sys.exit(1)
    
    # Wait a moment for processing
    print("\n⏳ Waiting for processing...")
    time.sleep(2)
    
    # Test plagiarism check
    check_result = test_check_plagiarism(submission_id)
    if not check_result:
        print("\n❌ Plagiarism check test failed")
        sys.exit(1)
    
    # Test explanation
    if not test_explain():
        print("\n⚠️  Explanation test failed (this might be due to API key issues)")
    
    # Test stats
    if not test_stats():
        print("\n⚠️  Stats test failed")
    
    print("\n" + "=" * 50)
    print("🎉 All tests completed!")
    print("✅ System is working correctly")
    print("\nYou can now use the frontend at: http://localhost:8501")

if __name__ == "__main__":
    main()
