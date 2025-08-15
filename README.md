# 🌍 Global Screen Share

A powerful, secure, and user-friendly screen sharing solution that works globally across different networks and platforms.

## ✨ Features

- **🌐 Global Access**: Share screens across different networks and locations
- **🔐 Secure**: SSL/TLS encryption and user authentication
- **📱 Cross-Platform**: Works on Windows, macOS, and Linux
- **🖥️ Multiple Viewers**: Support for multiple simultaneous viewers
- **📋 Clipboard Sync**: Real-time clipboard synchronization
- **🌐 Web Interface**: Modern web-based client for easy access
- **💻 Command Line**: Traditional command-line client for power users
- **🔧 Flexible**: Both relay server and direct connection modes

## 🏗️ Architecture

The system consists of three main components:

1. **Relay Server** (`global_server.py`) - Central server for global connectivity
2. **Global Client** (`global_client.py`) - Command-line client for host/viewer
3. **Web Client** (`web_client.py`) - Web-based interface for easy access

## 🚀 Quick Start

### 📋 Prerequisites

- Python 3.7 or higher
- All dependencies installed: `pip install -r requirements.txt`

### 🖥️ Setup Instructions

#### **Option 1: Easy Setup (Recommended)**
Run the deployment script to set up everything automatically:
```bash
python deploy.py
```

#### **Option 2: Windows Quick Start**
- **Server**: Double-click `start_server_windows.bat` to start the server
- **Host**: Double-click `start_host_windows.bat` to share your screen
- **Viewer**: Double-click `start_viewer_windows.bat` to watch a shared screen
- **List Sessions**: Double-click `list_sessions_windows.bat` to see active sessions

#### **Option 3: Manual Setup**

### 🖥️ **SERVER MACHINE** (Cloud/VPS/Network Server)

**Files to run on the server machine:**

1. **Start the Relay Server** (Required):
   ```bash
   python global_server.py
   ```
   - This creates the central server that handles all connections
   - Runs on port 8443 (SSL) by default
   - Creates default admin user: `admin` / `admin123`
   - Generates SSL certificates automatically

2. **Start the Web Interface** (Optional but recommended):
   ```bash
   python web_client.py
   ```
   - Provides a web interface at `http://your-server-ip:5000`
   - Allows users to share/view screens through a browser
   - No installation required for viewers

### 💻 **HOST MACHINE** (Person sharing their screen)

**Files to run on the host machine:**

**Option A: Web Interface (Easiest)**
1. Open browser and go to `http://your-server-ip:5000`
2. Click "Start Sharing"
3. Enter your name and grant screen capture permissions
4. Share the session ID with viewers

**Option B: Command Line**
```bash
# Windows (with batch file)
start_host_windows.bat

# Or manual command
python global_client.py --server your-server-ip --port 8443 --username admin --password admin123 --mode host --no-ssl
```

### 👁️ **VIEWER MACHINES** (People watching the screen)

**Files to run on viewer machines:**

**Option A: Web Interface (Easiest)**
1. Open browser and go to `http://your-server-ip:5000`
2. Click "Join Session"
3. Enter the session ID from the host
4. Enter your name

**Option B: Command Line**
```bash
# Windows (with batch file)
start_viewer_windows.bat

# Or manual command
python global_client.py --server your-server-ip --port 8443 --username admin --password admin123 --mode viewer --session SESSION_ID --no-ssl
```

### 🌐 **Network Configuration**

- **Local Network**: Use the server's local IP (e.g., `192.168.1.100`)
- **Internet**: Use the server's public IP or domain name
- **Firewall**: Open ports 8443 (SSL) and 5000 (Web) on the server

### 🆔 **Getting Session IDs**

There are several ways to get session IDs:

#### **Method 1: When Starting as Host (Automatic)**
When you start as a host, the session ID is automatically generated and displayed:
```bash
python global_client.py --server localhost --port 8443 --username admin --password admin123 --mode host --no-ssl
```
**Output:**
```
[+] Successfully authenticated as admin
[+] Session created: abc123def-4567-89ab-cdef-123456789abc
```

#### **Method 2: Web Interface (Easiest)**
1. Open browser: `http://localhost:5000`
2. Click "Start Sharing"
3. Enter your name
4. Click "Start Sharing"
5. **Session ID is displayed prominently on screen**

#### **Method 3: List Active Sessions**
```bash
# Windows
list_sessions_windows.bat

# Or manual command
python global_server.py --list-sessions
```

#### **Method 4: Server Console**
The server shows session creation in real-time:
```
[+] NEW SESSION CREATED: abc123def-4567-89ab-cdef-123456789abc
[+] Share this ID with viewers: abc123def-4567-89ab-cdef-123456789abc
```

## 📋 Detailed Usage

### 🌐 **Web Interface** (Recommended for most users)

**For Host (Screen Sharing):**
1. Open browser and navigate to `http://your-server-ip:5000`
2. Click "Start Sharing" button
3. Enter your name and optional session ID (or leave empty for auto-generation)
4. Click "Start Sharing"
5. Grant screen capture permissions when prompted
6. Share the displayed session ID with viewers

**For Viewers (Watching Screen):**
1. Open browser and navigate to `http://your-server-ip:5000`
2. Click "Join Session" button
3. Enter the session ID provided by the host
4. Enter your name
5. Click "Join Session"
6. Wait for the screen share to appear

### 💻 **Command Line Interface** (For advanced users)

#### Global Client Options

```bash
python global_client.py [OPTIONS]

Options:
  --server TEXT     Relay server hostname/IP [required]
  --port INTEGER    Server port (default: 8443)
  --username TEXT   Username for authentication [required]
  --password TEXT   Password for authentication [required]
  --mode TEXT       Client mode: host or viewer [required]
  --session TEXT    Session ID (required for viewer mode)
  --no-ssl          Disable SSL (not recommended)
```

#### Examples

**Start a screen sharing session (Host):**
```bash
python global_client.py --server 192.168.1.100 --port 8443 --username admin --password admin123 --mode host --no-ssl
```

**Join a session as viewer:**
```bash
python global_client.py --server 192.168.1.100 --port 8443 --username admin --password admin123 --mode viewer --session abc123def456 --no-ssl
```

**Connect to remote server:**
```bash
python global_client.py --server your-domain.com --username admin --password admin123 --mode host
```

## 🔧 Configuration

### Server Configuration

Edit `global_server.py` to customize:

```python
# Server settings
HOST = '0.0.0.0'  # Listen on all interfaces
PORT = 8443       # Server port
SSL_CERT = 'server.crt'  # SSL certificate path
SSL_KEY = 'server.key'   # SSL private key path
```

### SSL Certificates

For production, replace the self-signed certificates with proper SSL certificates:

```bash
# Generate proper SSL certificate
openssl req -x509 -newkey rsa:4096 -keyout server.key -out server.crt -days 365 -nodes -subj '/CN=your-domain.com'
```

### User Management

The server includes a simple user management system:

```python
# Create new user programmatically
server = RelayServer()
server.create_user('newuser', 'password123')
```

## 🌐 Deployment Scenarios

### 🏠 **Local Network Setup**

**Server Machine:**
1. Run `python global_server.py` on any machine in your network
2. Run `python web_client.py` (optional, for web interface)
3. Note the server's IP address (e.g., `192.168.1.100`)

**Host & Viewer Machines:**
- Use the server's local IP address to connect
- No internet required - works within your local network

### 🌍 **Internet Deployment**

**Server Machine (VPS/Cloud):**
1. Deploy to AWS, DigitalOcean, Google Cloud, etc.
2. Run `python global_server.py` on the cloud server
3. Run `python web_client.py` (optional, for web interface)
4. Configure firewall to allow ports 8443 and 5000
5. Use the server's public IP or domain name

**Host & Viewer Machines:**
- Can be anywhere in the world
- Connect using the server's public IP or domain name

### 🐳 **Docker Deployment** (Advanced)

**Server Machine:**
```bash
# Build and run with Docker
docker build -t screen-share .
docker run -p 8443:8443 -p 5000:5000 screen-share
```

**Or use docker-compose:**
```bash
docker-compose up -d
```

### 🔧 **Production Setup** (Recommended for business use)

**Server Machine:**
1. Use proper SSL certificates (not self-signed)
2. Set up reverse proxy (Nginx/Apache)
3. Configure domain name
4. Set up monitoring and logging

**Example Nginx configuration:**
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🔒 Security Features

- **SSL/TLS Encryption**: All communications are encrypted
- **User Authentication**: Username/password required for access
- **Session Management**: Unique session IDs for each sharing session
- **Input Validation**: Protection against malicious input
- **Rate Limiting**: Built-in protection against abuse

## 🛠️ Troubleshooting

### Common Issues

1. **OpenSSL not found error**:
   - **Windows**: Install OpenSSL from https://slproweb.com/products/Win32OpenSSL.html
   - **macOS**: `brew install openssl`
   - **Linux**: `sudo apt-get install openssl` (Ubuntu/Debian) or `sudo yum install openssl` (CentOS/RHEL)
   - **Alternative**: The server will automatically start without SSL if OpenSSL is not available

2. **Screen capture not working**:
   - Ensure screen recording permissions are granted
   - On macOS: System Preferences > Security & Privacy > Privacy > Screen Recording
   - On Windows: Allow the application through Windows Defender

3. **Connection refused**:
   - Check if the relay server is running
   - Verify the server IP and port
   - Check firewall settings

4. **SSL certificate errors**:
   - For testing: Use `--no-ssl` flag with the client
   - For production: Use proper SSL certificates

5. **Performance issues**:
   - Reduce screen capture quality in the code
   - Use a faster network connection
   - Consider using a server closer to users

6. **Connection refused error**:
   - **Issue**: `[WinError 10061] No connection could be made because the target machine actively refused it`
   - **Solution**: Make sure the server is running and use the correct port
   - **For non-SSL**: Use `--port 8443 --no-ssl` (server runs on 8443 but client connects without SSL)
   - **For SSL**: Use `--port 8443` (default, with SSL)
   - **Check server**: Run `netstat -an | findstr :8443` to verify server is listening

7. **Web client screen capture not working**:
   - **Issue**: "Screen preview not active" or "Screen capture not supported"
   - **Solution**: Use HTTPS mode for better browser compatibility
   - **Command**: `python web_client.py --https` or use `start_web_https.bat`
   - **Browser**: Allow screen sharing when prompted
   - **Alternative**: Try different browsers (Chrome, Firefox, Edge)
   - **Check console**: Open browser developer tools to see error messages

8. **System test**:
   - **Run**: `python test_system.py` or `test_system.bat`
   - **Purpose**: Check all dependencies and components
   - **Fix issues**: Install missing packages with `pip install -r requirements.txt`

### Logs

Check the log files for detailed error information:
- `relay_server.log` - Server logs
- Console output for client errors

## 🔄 Migration from Original

If you're migrating from the original `client.py` and `server.py`:

### **File Comparison:**

| Original System | Global System |
|----------------|---------------|
| `server.py` → `global_server.py` | Enhanced with authentication, SSL, multi-session support |
| `client.py` → `global_client.py` | Enhanced with authentication, SSL, viewer mode |
| N/A → `web_client.py` | New web interface for easy access |

### **Migration Path:**

1. **Keep original files** for simple local network use
2. **Use new global system** for internet access and advanced features
3. **Gradual migration** - both systems can run simultaneously
4. **Web interface** - easiest option for non-technical users

### **When to Use Which:**

- **Original System**: Simple local network sharing, no authentication needed
- **Global System**: Internet access, multiple sessions, security, web interface

## 📈 Performance Optimization

- **Compression**: Images are compressed using JPEG (60% quality)
- **Frame Rate**: Configurable frame rate (default: 10 FPS)
- **Resolution**: Automatic scaling to fit viewer's screen
- **Bandwidth**: Adaptive quality based on network conditions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section below
2. Review the logs for error messages
3. Create an issue on GitHub with detailed information

## 📋 **Quick Reference - Which File on Which Machine**

| Machine Type | Files to Run | Purpose |
|--------------|--------------|---------|
| **Server** (Cloud/VPS/Network) | `global_server.py` + `web_client.py` | Central relay server + web interface |
| **Host** (Sharing screen) | Browser or `global_client.py` | Share screen with others |
| **Viewer** (Watching screen) | Browser or `global_client.py` | Watch shared screens |
| **Admin** (Managing sessions) | `list_sessions_windows.bat` or `global_server.py --list-sessions` | List active sessions |

### **Network Addresses:**
- **Local Network**: `http://192.168.1.100:5000` (web) or `192.168.1.100:8443` (CLI)
- **Internet**: `http://your-domain.com:5000` (web) or `your-domain.com:8443` (CLI)

---

**Happy Screen Sharing! 🎉**
