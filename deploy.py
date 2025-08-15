#!/usr/bin/env python3
"""
Deployment script for Global Screen Share
Helps users set up the system quickly and easily
"""

import os
import sys
import subprocess
import platform
import argparse
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        print("Try running: pip install -r requirements.txt")
        sys.exit(1)

def create_directories():
    """Create necessary directories"""
    directories = ["templates", "static", "logs"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    print("✅ Directories created")

def generate_ssl_certificates():
    """Generate SSL certificates for testing"""
    if os.path.exists("server.crt") and os.path.exists("server.key"):
        print("✅ SSL certificates already exist")
        return
    
    print("🔐 Generating SSL certificates...")
    try:
        subprocess.run([
            "openssl", "req", "-x509", "-newkey", "rsa:4096", 
            "-keyout", "server.key", "-out", "server.crt", 
            "-days", "365", "-nodes", "-subj", "/CN=localhost"
        ], check=True, capture_output=True)
        print("✅ SSL certificates generated")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  OpenSSL not found. SSL certificates will be generated when server starts.")
        print("   Install OpenSSL or use --no-ssl flag for testing")

def create_config_file():
    """Create a basic configuration file"""
    config_content = """# Global Screen Share Configuration

[server]
host = 0.0.0.0
port = 8443
ssl_enabled = true
ssl_cert = server.crt
ssl_key = server.key

[security]
default_username = admin
default_password = admin123
max_connections = 100

[performance]
frame_rate = 10
image_quality = 60
max_clipboard_size = 1048576

[logging]
level = INFO
file = logs/relay_server.log
"""
    
    with open("config.ini", "w") as f:
        f.write(config_content)
    print("✅ Configuration file created")

def create_startup_scripts():
    """Create startup scripts for different platforms"""
    system = platform.system().lower()
    
    if system == "windows":
        # Windows batch file
        batch_content = """@echo off
echo Starting Global Screen Share Server...
python global_server.py
pause
"""
        with open("start_server.bat", "w") as f:
            f.write(batch_content)
        
        web_batch_content = """@echo off
echo Starting Web Client...
python web_client.py
pause
"""
        with open("start_web.bat", "w") as f:
            f.write(web_batch_content)
        
        print("✅ Windows startup scripts created")
        
    else:
        # Unix shell script
        shell_content = """#!/bin/bash
echo "Starting Global Screen Share Server..."
python3 global_server.py
"""
        with open("start_server.sh", "w") as f:
            f.write(shell_content)
        
        web_shell_content = """#!/bin/bash
echo "Starting Web Client..."
python3 web_client.py
"""
        with open("start_web.sh", "w") as f:
            f.write(web_shell_content)
        
        # Make executable
        os.chmod("start_server.sh", 0o755)
        os.chmod("start_web.sh", 0o755)
        
        print("✅ Unix startup scripts created")

def create_dockerfile():
    """Create Dockerfile for containerized deployment"""
    dockerfile_content = """FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    openssl \\
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create necessary directories
RUN mkdir -p templates static logs

# Generate SSL certificates
RUN openssl req -x509 -newkey rsa:4096 \\
    -keyout server.key -out server.crt \\
    -days 365 -nodes -subj '/CN=localhost'

# Expose ports
EXPOSE 8443 5000

# Start the server
CMD ["python", "global_server.py"]
"""
    
    with open("Dockerfile", "w") as f:
        f.write(dockerfile_content)
    
    # Create docker-compose.yml
    compose_content = """version: '3.8'

services:
  screen-share-server:
    build: .
    ports:
      - "8443:8443"
      - "5000:5000"
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    environment:
      - PYTHONUNBUFFERED=1
"""
    
    with open("docker-compose.yml", "w") as f:
        f.write(compose_content)
    
    print("✅ Docker files created")

def run_tests():
    """Run basic tests to ensure everything works"""
    print("🧪 Running basic tests...")
    
    # Test imports
    try:
        import flask
        import cv2
        import numpy
        import socket
        import ssl
        print("✅ All required modules can be imported")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Test SSL certificate generation
    try:
        if not os.path.exists("server.crt"):
            generate_ssl_certificates()
    except Exception as e:
        print(f"⚠️  SSL certificate test failed: {e}")
    
    print("✅ Basic tests completed")
    return True

def show_next_steps():
    """Show next steps for the user"""
    print("\n" + "="*50)
    print("🎉 DEPLOYMENT COMPLETE!")
    print("="*50)
    
    system = platform.system().lower()
    
    print("\n📋 Next Steps:")
    print("1. Start the relay server:")
    if system == "windows":
        print("   - Double-click 'start_server.bat' or")
        print("   - Run: python global_server.py")
    else:
        print("   - Run: ./start_server.sh or")
        print("   - Run: python3 global_server.py")
    
    print("\n2. Start the web client:")
    if system == "windows":
        print("   - Double-click 'start_web.bat' or")
        print("   - Run: python web_client.py")
    else:
        print("   - Run: ./start_web.sh or")
        print("   - Run: python3 web_client.py")
    
    print("\n3. Access the web interface:")
    print("   - Open browser to: http://localhost:5000")
    
    print("\n4. Use command line client:")
    print("   - Host: python global_client.py --server localhost --username admin --password admin123 --mode host")
    print("   - Viewer: python global_client.py --server localhost --username admin --password admin123 --mode viewer --session SESSION_ID")
    
    print("\n🔧 Configuration:")
    print("   - Edit config.ini to customize settings")
    print("   - Default admin credentials: admin/admin123")
    print("   - Server runs on port 8443 (SSL) and 5000 (Web)")
    
    print("\n🌐 For Internet Access:")
    print("   - Deploy to a VPS/cloud server")
    print("   - Configure domain name and proper SSL certificates")
    print("   - Use Docker: docker-compose up -d")
    
    print("\n📚 Documentation:")
    print("   - Read README.md for detailed instructions")
    print("   - Check logs/ directory for troubleshooting")

def main():
    parser = argparse.ArgumentParser(description="Deploy Global Screen Share")
    parser.add_argument("--skip-deps", action="store_true", help="Skip dependency installation")
    parser.add_argument("--skip-ssl", action="store_true", help="Skip SSL certificate generation")
    parser.add_argument("--docker", action="store_true", help="Create Docker files")
    parser.add_argument("--test", action="store_true", help="Run tests only")
    
    args = parser.parse_args()
    
    print("🚀 Global Screen Share Deployment")
    print("="*40)
    
    if args.test:
        run_tests()
        return
    
    # Check Python version
    check_python_version()
    
    # Install dependencies
    if not args.skip_deps:
        install_dependencies()
    
    # Create directories
    create_directories()
    
    # Generate SSL certificates
    if not args.skip_ssl:
        generate_ssl_certificates()
    
    # Create configuration
    create_config_file()
    
    # Create startup scripts
    create_startup_scripts()
    
    # Create Docker files if requested
    if args.docker:
        create_dockerfile()
    
    # Run tests
    run_tests()
    
    # Show next steps
    show_next_steps()

if __name__ == "__main__":
    main()
