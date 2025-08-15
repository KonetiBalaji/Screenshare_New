#!/usr/bin/env python3
"""
System Test Script for Global Screen Share
Tests all components and dependencies
"""

import sys
import os
import importlib
import subprocess
import socket
import threading
import time

def test_import(module_name, package_name=None):
    """Test if a module can be imported"""
    try:
        importlib.import_module(module_name)
        print(f"[✓] {package_name or module_name} - OK")
        return True
    except ImportError as e:
        print(f"[✗] {package_name or module_name} - FAILED: {e}")
        return False

def test_python_version():
    """Test Python version compatibility"""
    version = sys.version_info
    print(f"[i] Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 8:
        print("[✓] Python version - OK")
        return True
    else:
        print("[✗] Python version - FAILED: Python 3.8+ required")
        return False

def test_dependencies():
    """Test all required dependencies"""
    print("\n=== Testing Dependencies ===")
    
    dependencies = [
        ('flask', 'Flask'),
        ('flask_socketio', 'Flask-SocketIO'),
        ('cv2', 'OpenCV'),
        ('numpy', 'NumPy'),
        ('PIL', 'Pillow'),
        ('pyperclip', 'Pyperclip'),
        ('screeninfo', 'Screeninfo'),
        ('pyautogui', 'PyAutoGUI'),
        ('keyboard', 'Keyboard'),
        ('pystray', 'Pystray'),
        ('cryptography', 'Cryptography'),
        ('requests', 'Requests'),
        ('dotenv', 'Python-dotenv'),
        ('eventlet', 'Eventlet'),
    ]
    
    results = []
    for module, package in dependencies:
        results.append(test_import(module, package))
    
    return all(results)

def test_file_structure():
    """Test if all required files exist"""
    print("\n=== Testing File Structure ===")
    
    required_files = [
        'global_server.py',
        'global_client.py',
        'web_client.py',
        'requirements.txt',
        'README.md',
        'templates/host.html',
        'templates/viewer.html',
        'templates/index.html',
        'start_server_windows.bat',
        'start_host_windows.bat',
        'start_viewer_windows.bat',
    ]
    
    results = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"[✓] {file_path} - OK")
            results.append(True)
        else:
            print(f"[✗] {file_path} - MISSING")
            results.append(False)
    
    return all(results)

def test_ssl_certificates():
    """Test SSL certificate generation"""
    print("\n=== Testing SSL Certificates ===")
    
    try:
        result = subprocess.run([
            'openssl', 'version'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print(f"[✓] OpenSSL available: {result.stdout.strip()}")
            return True
        else:
            print("[✗] OpenSSL not working properly")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("[!] OpenSSL not found - SSL features will be disabled")
        print("[i] System can still run without SSL (insecure mode)")
        return True  # Not critical for basic functionality

def test_network_ports():
    """Test if required ports are available"""
    print("\n=== Testing Network Ports ===")
    
    ports_to_test = [5000, 8443, 9999]
    results = []
    
    for port in ports_to_test:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                print(f"[✓] Port {port} - AVAILABLE")
                results.append(True)
        except OSError:
            print(f"[✗] Port {port} - IN USE")
            results.append(False)
    
    return all(results)

def test_web_client():
    """Test web client functionality"""
    print("\n=== Testing Web Client ===")
    
    try:
        # Test basic Flask app creation
        from flask import Flask
        from flask_socketio import SocketIO
        
        app = Flask(__name__)
        socketio = SocketIO(app)
        
        print("[✓] Flask app creation - OK")
        print("[✓] SocketIO initialization - OK")
        return True
    except Exception as e:
        print(f"[✗] Web client test failed: {e}")
        return False

def test_screen_capture():
    """Test screen capture capabilities"""
    print("\n=== Testing Screen Capture ===")
    
    # Test PIL
    try:
        from PIL import ImageGrab
        print("[✓] PIL ImageGrab - OK")
        pil_ok = True
    except ImportError:
        print("[✗] PIL ImageGrab - FAILED")
        pil_ok = False
    
    # Test OpenCV
    try:
        import cv2
        print("[✓] OpenCV - OK")
        cv2_ok = True
    except ImportError:
        print("[✗] OpenCV - FAILED")
        cv2_ok = False
    
    # Test screeninfo
    try:
        from screeninfo import get_monitors
        monitors = get_monitors()
        print(f"[✓] Screeninfo - OK (found {len(monitors)} monitors)")
        screeninfo_ok = True
    except ImportError:
        print("[✗] Screeninfo - FAILED")
        screeninfo_ok = False
    
    return pil_ok or cv2_ok

def test_clipboard():
    """Test clipboard functionality"""
    print("\n=== Testing Clipboard ===")
    
    try:
        import pyperclip
        print("[✓] Pyperclip - OK")
        return True
    except ImportError:
        print("[✗] Pyperclip - FAILED")
        return False

def generate_report(results):
    """Generate a test report"""
    print("\n" + "="*50)
    print("SYSTEM TEST REPORT")
    print("="*50)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    failed_tests = total_tests - passed_tests
    
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    
    if failed_tests == 0:
        print("\n[✓] ALL TESTS PASSED - System is ready!")
    else:
        print(f"\n[✗] {failed_tests} TESTS FAILED")
        print("\nFailed components:")
        for test_name, result in results.items():
            if not result:
                print(f"  - {test_name}")
        
        print("\nRecommendations:")
        print("1. Install missing dependencies: pip install -r requirements.txt")
        print("2. Check file permissions and paths")
        print("3. Ensure ports are not in use by other applications")
        print("4. For screen capture issues, try running with HTTPS")

def main():
    """Run all tests"""
    print("Global Screen Share - System Test")
    print("="*40)
    
    results = {}
    
    # Run all tests
    results['Python Version'] = test_python_version()
    results['Dependencies'] = test_dependencies()
    results['File Structure'] = test_file_structure()
    results['SSL Certificates'] = test_ssl_certificates()
    results['Network Ports'] = test_network_ports()
    results['Web Client'] = test_web_client()
    results['Screen Capture'] = test_screen_capture()
    results['Clipboard'] = test_clipboard()
    
    # Generate report
    generate_report(results)
    
    return all(results.values())

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
